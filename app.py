import streamlit as st
from pypdf import PdfWriter, errors
from io import BytesIO
from streamlit.runtime.uploaded_file_manager import UploadedFile
from streamlit_sortables import sort_items

def validate_password(password: str) -> bool:
    """
    Kontrollerar om lösenordet uppfyller säkerhetskraven.

    Args:
        password (str): Lösenordet som ska valideras.

    Returns:
        bool: True om lösenordet innehåller minst en stor bokstav och en siffra, annars False.
    """
    if not password:
        return False
        
    has_upper = any(char.isupper() for char in password)
    has_digit = any(char.isdigit() for char in password)
    
    return has_upper and has_digit

def merge_pdfs(ordered_files: list[UploadedFile], password: str = "") -> BytesIO | None:
    """
    Slår ihop en lista med PDF-filer i minnet och krypterar filen om ett lösenord anges.

    Args:
        ordered_files (list[UploadedFile]): Lista med filer i den ordning de ska slås ihop.
        password (str, optional): Lösenord för att skydda den nya PDF-filen. Standard är tom sträng.

    Returns:
        BytesIO | None: En byteström av den sammanslagna PDF:en, eller None om ett fel uppstår.
    """
    merger = PdfWriter()
    merged_pdf_stream = BytesIO()
    
    try:
        for pdf_file in ordered_files:
            merger.append(pdf_file)
            
        # Lägg till lösenordsskydd om användaren har valt det och fyllt i ett godkänt lösenord
        if password:
            merger.encrypt(password)
            
        merger.write(merged_pdf_stream)
        merged_pdf_stream.seek(0)
        return merged_pdf_stream
        
    except errors.PdfReadError as read_error:
        st.error(f"Kunde inte läsa en av PDF-filerna. Den kan vara korrupt eller redan lösenordsskyddad:\n{read_error}")
        return None
    except Exception as e:
        st.error(f"Ett oväntat fel uppstod vid sammanslagningen:\n{e}")
        return None
    finally:
        merger.close()

def main() -> None:
    """Huvudfunktionen som bygger Streamlit-gränssnittet."""
    st.set_page_config(page_title="PDF-Sammanslagning", page_icon="📄")
    
    # Lade till PDF-ikonen i rubriken här
    st.title("📄 Slå ihop PDF-filer")
    
    # 1. Filuppladdning
    uploaded_files = st.file_uploader(
        "Ladda upp PDF-filer", 
        type="pdf", 
        accept_multiple_files=True
    )

    if uploaded_files:
        file_dict: dict[str, UploadedFile] = {file.name: file for file in uploaded_files}
        original_names: list[str] = list(file_dict.keys())
        
        st.subheader("Ändra ordning på filerna")
        st.write("Klicka och dra filnamnen i listan nedan för att placera dem i den ordning du vill ha dem.")
        
        # 2. Dra-och-släpp sortering
        sorted_names = sort_items(original_names)
        
        st.divider()
        
        # 3. Namnge, lösenordsskydda och exportera
        output_name = st.text_input("Vad ska den nya filen heta?", value="sammanslagen.pdf")
        
        # UI för lösenordsskydd
        use_password = st.checkbox("Skydda filen med lösenord")
        password_input = ""
        
        if use_password:
            password_input = st.text_input(
                "Ange lösenord (krav: minst en stor bokstav och en siffra):", 
                type="password"
            )
        
        if st.button("Skapa sammanslagen PDF", type="primary"):
            if not sorted_names:
                st.warning("Inga filer finns att slå ihop.")
                return
                
            # Validera lösenordet innan vi försöker slå ihop filerna
            if use_password and not validate_password(password_input):
                st.error("Lösenordet uppfyller inte kraven. Se till att ha minst en stor bokstav och en siffra.")
                return
                
            if not output_name.lower().endswith(".pdf"):
                output_name += ".pdf"
                
            ordered_files = [file_dict[name] for name in sorted_names]
            
            with st.spinner("Slår ihop filerna..."):
                # Skicka med lösenordet till funktionen (blir en tom sträng om checkboxen inte är ipekad)
                merged_file = merge_pdfs(ordered_files, password_input if use_password else "")
                
                if merged_file:
                    if use_password:
                        st.success("Filerna har slagits ihop och är nu lösenordsskyddade! 🔒")
                    else:
                        st.success("Filerna har slagits ihop!")
                        
                    st.download_button(
                        label=f"Ladda ner {output_name}",
                        data=merged_file,
                        file_name=output_name,
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
