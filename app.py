import streamlit as st
from pypdf import PdfWriter
from io import BytesIO
from streamlit.runtime.uploaded_file_manager import UploadedFile

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
        # Återställ pekaren till början av filen så att den kan läsas vid nedladdning
        merged_pdf_stream.seek(0)
        return merged_pdf_stream
        
    except Exception as e:
        st.error(f"Ett oväntat fel uppstod vid sammanslagningen: {e}")
        return None
    finally:
        merger.close()

def main() -> None:
    """Huvudfunktionen som bygger Streamlit-gränssnittet."""
    st.set_page_config(page_title="PDF-Sammanslagning", page_icon="📄")
    st.title("Slå ihop PDF-filer")
    
    st.markdown("1. **Dra och släpp** dina PDF-filer i rutan nedan.\n"
                "2. **Välj ordning** i rullgardinsmenyn.\n"
                "3. **Ladda ner** din nya fil.")

    # 1. Filuppladdning (drag-and-drop)
    uploaded_files = st.file_uploader(
        "Ladda upp PDF-filer", 
        type="pdf", 
        accept_multiple_files=True
    )

    if uploaded_files:
        # Skapa en dictionary för att snabbt hitta filobjektet baserat på filnamnet
        file_dict: dict[str, UploadedFile] = {file.name: file for file in uploaded_files}
        
        st.subheader("Välj ordning")
        st.write("Ta bort och lägg till filerna nedan i exakt den ordning du vill att de ska slås ihop:")
        
        # 2. Välj ordning
        ordered_file_names = st.multiselect(
            "Ordning för export:",
            options=list(file_dict.keys()),
            default=list(file_dict.keys())
        )
        
        st.divider()
        
        # 3. Namnge och exportera
        output_name = st.text_input("Vad ska den nya filen heta?", value="sammanslagen.pdf")
        
        if st.button("Skapa sammanslagen PDF", type="primary"):
            if not ordered_file_names:
                st.warning("Du måste ha minst en fil i listan för att kunna slå ihop.")
                return
                
            if not output_name.lower().endswith(".pdf"):
                output_name += ".pdf"
                
            ordered_files = [file_dict[name] for name in ordered_file_names]
            
            with st.spinner("Slår ihop..."):
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