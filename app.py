import streamlit as st
from pypdf import PdfWriter, errors
from io import BytesIO
from streamlit.runtime.uploaded_file_manager import UploadedFile

def initialize_state() -> None:
    """Initierar session state för att hålla reda på filernas ordning över omladdningar."""
    if "file_order" not in st.session_state:
        st.session_state.file_order = []

def move_up(index: int) -> None:
    """
    Flyttar en fil ett steg uppåt i den sparade ordningen.

    Args:
        index (int): Den nuvarande positionen för filen i listan.
    """
    if index > 0:
        order = st.session_state.file_order
        order[index - 1], order[index] = order[index], order[index - 1]

def move_down(index: int) -> None:
    """
    Flyttar en fil ett steg nedåt i den sparade ordningen.

    Args:
        index (int): Den nuvarande positionen för filen i listan.
    """
    order = st.session_state.file_order
    if index < len(order) - 1:
        order[index + 1], order[index] = order[index], order[index + 1]

def sync_uploaded_files(uploaded_files: list[UploadedFile]) -> dict[str, UploadedFile]:
    """
    Synkroniserar de uppladdade filerna med den sparade ordningen i session state.
    
    Args:
        uploaded_files (list[UploadedFile]): Listan med filer från uppladdningskomponenten.
        
    Returns:
        dict[str, UploadedFile]: Ett lexikon som mappar filnamn till filobjekt.
    """
    file_dict: dict[str, UploadedFile] = {file.name: file for file in uploaded_files}
    current_names = list(file_dict.keys())
    
    # Lägg till nya filer i slutet av ordningslistan
    for name in current_names:
        if name not in st.session_state.file_order:
            st.session_state.file_order.append(name)
            
    # Rensa bort filer ur ordningslistan som användaren har klickat bort
    st.session_state.file_order = [
        name for name in st.session_state.file_order if name in current_names
    ]
    
    return file_dict

def merge_pdfs(ordered_files: list[UploadedFile]) -> BytesIO | None:
    """
    Slår ihop en lista med PDF-filer i minnet.

    Args:
        ordered_files (list[UploadedFile]): Lista med filer i den ordning de ska slås ihop.

    Returns:
        BytesIO | None: En byteström av den sammanslagna PDF:en, eller None om ett fel uppstår.
    """
    merger = PdfWriter()
    merged_pdf_stream = BytesIO()
    
    try:
        for pdf_file in ordered_files:
            merger.append(pdf_file)
            
        merger.write(merged_pdf_stream)
        merged_pdf_stream.seek(0)
        return merged_pdf_stream
        
    except errors.PdfReadError as read_error:
        st.error(f"Kunde inte läsa en av PDF-filerna. Den kan vara korrupt eller lösenordsskyddad:\n{read_error}")
        return None
    except Exception as e:
        st.error(f"Ett oväntat fel uppstod vid sammanslagningen:\n{e}")
        return None
    finally:
        merger.close()

def main() -> None:
    """Huvudfunktionen som bygger Streamlit-gränssnittet."""
    st.set_page_config(page_title="PDF-Sammanslagning", page_icon="📄")
    st.title("Slå ihop PDF-filer")
    
    initialize_state()

    # 1. Filuppladdning (drag-and-drop)
    uploaded_files = st.file_uploader(
        "Ladda upp PDF-filer", 
        type="pdf", 
        accept_multiple_files=True
    )

    if uploaded_files:
        file_dict = sync_uploaded_files(uploaded_files)
        
        st.subheader("Ändra ordning på filerna")
        st.write("Använd pilarna för att flytta filerna upp eller ner i listan så att de hamnar i rätt ordning.")
        
        # 2. Interaktiv lista för att styra ordningen
        for i, filename in enumerate(st.session_state.file_order):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.write(f"**{i + 1}.** {filename}")
            with col2:
                # Anropar move_up-funktionen direkt när knappen trycks
                st.button("⬆️", key=f"up_{i}", on_click=move_up, args=(i,))
            with col3:
                # Anropar move_down-funktionen direkt när knappen trycks
                st.button("⬇️", key=f"down_{i}", on_click=move_down, args=(i,))
                
        st.divider()
        
        # 3. Namnge och exportera
        output_name = st.text_input("Vad ska den nya filen heta?", value="sammanslagen.pdf")
        
        if st.button("Skapa sammanslagen PDF", type="primary"):
            if not st.session_state.file_order:
                st.warning("Inga filer finns att slå ihop.")
                return
                
            if not output_name.lower().endswith(".pdf"):
                output_name += ".pdf"
                
            # Hämta de faktiska filobjekten i den ordning användaren valt
            ordered_files = [file_dict[name] for name in st.session_state.file_order]
            
            with st.spinner("Slår ihop filerna..."):
                merged_file = merge_pdfs(ordered_files)
                
                if merged_file:
                    st.success("Filerna har slagits ihop!")
                    st.download_button(
                        label=f"Ladda ner {output_name}",
                        data=merged_file,
                        file_name=output_name,
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
