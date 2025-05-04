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
        
        self.mode.trace_add("write", self.update_mode_display)

        self.image_path = ctk.StringVar()
        self.file_path = ctk.StringVar()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.setup_ui()
        
        self.update_mode_display()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        ctk.CTkLabel(self.main_frame, text="Image (PNG only):").pack(anchor="w", pady=(0, 5))
        
        image_frame = ctk.CTkFrame(self.main_frame)
        image_frame.pack(fill="x", pady=(0, 15))
        
        image_entry = ctk.CTkEntry(image_frame, textvariable=self.image_path, width=400)
        image_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ctk.CTkButton(image_frame, text="Browse Image", command=self.browse_image).pack(side="right")

        ctk.CTkLabel(self.main_frame, text="Mode:").pack(anchor="w", pady=(0, 5))
        
        mode_frame = ctk.CTkFrame(self.main_frame)
        mode_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkRadioButton(mode_frame, text="Message", variable=self.mode, value="Message").pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(mode_frame, text="File", variable=self.mode, value="File").pack(side="left")

        self.message_frame = ctk.CTkFrame(self.main_frame)
        self.message_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(self.message_frame, text="Message:").pack(anchor="w", pady=(0, 5))
        self.message_box = ctk.CTkTextbox(self.message_frame, height=100, width=400)
        self.message_box.pack(fill="x")

        self.file_frame = ctk.CTkFrame(self.main_frame)
        
        ctk.CTkLabel(self.file_frame, text="File:").pack(anchor="w", pady=(0, 5))
        
        file_select_frame = ctk.CTkFrame(self.file_frame)
        file_select_frame.pack(fill="x")
        
        ctk.CTkEntry(file_select_frame, textvariable=self.file_path, width=400).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(file_select_frame, text="Browse File", command=self.browse_file).pack(side="right")

        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(button_frame, text="Encode", command=self.encode).pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(button_frame, text="Decode", command=self.decode).pack(side="right", fill="x", expand=True)

    def update_mode_display(self, *args):
        current_mode = self.mode.get()
        
        self.message_frame.pack_forget()
        self.file_frame.pack_forget()
        
        if current_mode == "Message":
            self.message_frame.pack(fill="x", pady=(0, 15), after=self.main_frame.winfo_children()[3])
        else:
            self.file_frame.pack(fill="x", pady=(0, 15), after=self.main_frame.winfo_children()[3])

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

        if self.mode.get() == "Message":
            text = self.message_box.get("0.0", "end").strip()
            if not text:
                messagebox.showerror("Error", "Please enter a message.")
                return
                
            data = TEXT_TYPE + text.encode('utf-8')
        else:
            file_path = self.file_path.get()
            if not os.path.isfile(file_path):
                messagebox.showerror("Error", "Please select a valid file.")
                return
                
            try:
                _, file_ext = os.path.splitext(file_path)
                
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:
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

        output_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG images", "*.png")]
        )
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
            decoded_data = decode_data_from_image(image)
            
            if decoded_data.startswith(TEXT_TYPE):
                text = decoded_data[len(TEXT_TYPE):].decode('utf-8')
                messagebox.showinfo("Decoded Text", text)
                
            elif decoded_data.startswith(FILE_TYPE):
                file_data = decoded_data[len(FILE_TYPE):]
                
                ext_len = struct.unpack('!H', file_data[:2])[0]
                
                ext = file_data[2:2+ext_len].decode('utf-8')
                
                content = file_data[2+ext_len:]
                
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
