import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import struct
from stego_core import encode_data_to_image, decode_data_from_image

TEXT_TYPE = b'TXT:'  
FILE_TYPE = b'FILE:'

class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Steganography App")
        self.mode = ctk.StringVar(value="Message")

        self.image_path = ctk.StringVar()
        self.file_path = ctk.StringVar()

        # Set appearance mode and default theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Image selection
        ctk.CTkLabel(main_frame, text="Image (PNG only):").pack(anchor="w", pady=(0, 5))
        
        image_frame = ctk.CTkFrame(main_frame)
        image_frame.pack(fill="x", pady=(0, 15))
        
        image_entry = ctk.CTkEntry(image_frame, textvariable=self.image_path, width=400)
        image_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(image_frame, text="Browse Image", command=self.browse_image).pack(side="right")

        # Mode selection
        ctk.CTkLabel(main_frame, text="Mode:").pack(anchor="w", pady=(0, 5))
        
        mode_frame = ctk.CTkFrame(main_frame)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkRadioButton(mode_frame, text="Message", variable=self.mode, value="Message").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(mode_frame, text="File", variable=self.mode, value="File").pack(side="left")

        # Message input
        ctk.CTkLabel(main_frame, text="Message:").pack(anchor="w", pady=(0, 5))
        self.message_box = ctk.CTkTextbox(main_frame, height=100, width=400)
        self.message_box.pack(fill="x", pady=(0, 15))

        # File selection
        ctk.CTkLabel(main_frame, text="File (for File mode):").pack(anchor="w", pady=(0, 5))
        
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkEntry(file_frame, textvariable=self.file_path, width=400).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(file_frame, text="Browse File", command=self.browse_file).pack(side="right")

        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(button_frame, text="Encode", command=self.encode).pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(button_frame, text="Decode", command=self.decode).pack(side="right", fill="x", expand=True)

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG images", "*.png")])
        if path:
            self.image_path.set(path)

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path.set(path)

    def encode(self):
        image = self.image_path.get()
        if not image:
            messagebox.showerror("Error", "Please select an image.")
            return

        # Prepare the data
        if self.mode.get() == "Message":
            text = self.message_box.get("0.0", "end").strip()
            if not text:
                messagebox.showerror("Error", "Please enter a message.")
                return
                
            # Encode text
            data = TEXT_TYPE + text.encode('utf-8')
        else:
            file_path = self.file_path.get()
            if not os.path.isfile(file_path):
                messagebox.showerror("Error", "Please select a valid file.")
                return
                
            try:
                _, file_ext = os.path.splitext(file_path)
                
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10 MB max warning
                    proceed = messagebox.askyesno(
                        "Large File Warning", 
                        f"The selected file is {file_size/1024/1024:.2f} MB. "
                        "Encoding large files may take time and require a large image. Continue?"
                    )
                    if not proceed:
                        return
                
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                ext_bytes = file_ext.encode('utf-8')
                ext_len = len(ext_bytes)
                
                ext_len_bytes = struct.pack('!H', ext_len)
                
                data = FILE_TYPE + ext_len_bytes + ext_bytes + file_data
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {str(e)}")
                return

        # Save the encoded image
        output_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG images", "*.png")]
        )
        # If user cancels the save
        if not output_path:
            return
            
        try:
            encode_data_to_image(image, data, output_path, compress=True)
            messagebox.showinfo(
                "Success", 
                f"Data encoded successfully to {output_path}\n"
                f"Original data size: {len(data)/1024:.2f} KB"
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Encoding failed: {str(e)}")

    def decode(self):
        image = self.image_path.get()
        if not image:
            messagebox.showerror("Error", "Please select an image.")
            return
            
        try:
            # Decode data from the image
            decoded_data = decode_data_from_image(image)
            
            # Check if it's text data
            if decoded_data.startswith(TEXT_TYPE):
                # Display the text message
                text = decoded_data[len(TEXT_TYPE):].decode('utf-8')
                messagebox.showinfo("Decoded Text", text)
                
            elif decoded_data.startswith(FILE_TYPE):
                file_data = decoded_data[len(FILE_TYPE):]
                
                ext_len = struct.unpack('!H', file_data[:2])[0]
                
                ext = file_data[2:2+ext_len].decode('utf-8')
                
                content = file_data[2+ext_len:]
                
                # Save the decoded file
                save_path = filedialog.asksaveasfilename(
                    defaultextension=ext,
                    filetypes=[("All files", "*.*")]
                )
                
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(content)
                    messagebox.showinfo(
                        "Success", 
                        f"File decoded and saved to {save_path}\n"
                        f"File size: {len(content)/1024:.2f} KB"
                    )
            #If file data is not correct
            else:
                try:
                    text = decoded_data.decode('utf-8')
                    messagebox.showinfo("Decoded Text (Legacy Format)", text)
                except UnicodeDecodeError:
                    save_path = filedialog.asksaveasfilename(
                        title="Save decoded binary data",
                        filetypes=[("All files", "*.*")]
                    )
                    
                    if save_path:
                        with open(save_path, 'wb') as f:
                            f.write(decoded_data)
                        messagebox.showinfo(
                            "Success", 
                            f"Binary data saved to {save_path}\n"
                            f"File size: {len(decoded_data)/1024:.2f} KB"
                        )
                        
        except Exception as e:
            messagebox.showerror("Error", f"Decoding failed: {str(e)}")
