import streamlit as st
from pypdf import PdfWriter, errors
from io import BytesIO
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit_sortables import sort_items

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
    
    # 1. Filuppladdning
    uploaded_files = st.file_uploader(
        "Ladda upp PDF-filer", 
        type="pdf", 
        accept_multiple_files=True
    )

    if uploaded_files:
        # Skapa en dictionary för att koppla filnamn till filobjekt
        file_dict: dict[str, UploadedFile] = {file.name: file for file in uploaded_files}
        original_names: list[str] = list(file_dict.keys())
        
        st.subheader("Ändra ordning på filerna")
        st.write("Klicka och dra filnamnen i listan nedan för att placera dem i den ordning du vill ha dem.")
        
        # 2. Dra-och-släpp sortering
        sorted_names = sort_items(original_names)
        
        st.divider()
        
        # 3. Namnge och exportera
        output_name = st.text_input("Vad ska den nya filen heta?", value="sammanslagen.pdf")
        
        if st.button("Skapa sammanslagen PDF", type="primary"):
            if not sorted_names:
                st.warning("Inga filer finns att slå ihop.")
                return
                
            if not output_name.lower().endswith(".pdf"):
                output_name += ".pdf"
                
            # Hämta filobjekten i den nya sorterade ordningen
            ordered_files = [file_dict[name] for name in sorted_names]
            
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
