import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import struct
import threading
import queue
import time
from stego_core import encode_data_to_image, decode_data_from_image

# Constants for data type identification
TEXT_TYPE = b'TXT:'
FILE_TYPE = b'FILE:'

class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cicada Steganography")
        self.root.geometry("900x680")
        self.root.minsize(800, 600)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.mode = ctk.StringVar(value="Message")
        self.mode.trace_add("write", self.update_mode_display)
        self.image_path = ctk.StringVar()
        self.image_path.trace_add("write", self.update_image_preview)
        self.file_path = ctk.StringVar()
        self.status_text = ctk.StringVar(value="Ready")
        
        # Image preview
        self.preview_image = None
        
        self.setup_ui()
        self.update_mode_display()

    def setup_ui(self):
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tabs = ctk.CTkTabview(self.main_container)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tabs
        self.encode_tab = self.tabs.add("Encode")
        self.decode_tab = self.tabs.add("Decode")
        
        self.setup_encode_tab()
        
        self.setup_decode_tab()
        
        status_frame = ctk.CTkFrame(self.main_container, height=30)
        status_frame.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(status_frame, textvariable=self.status_text).pack(side="left", padx=10)
    
    def setup_encode_tab(self):
        left_frame = ctk.CTkFrame(self.encode_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=10)
        
        right_frame = ctk.CTkFrame(self.encode_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=10)
        
        title_label = ctk.CTkLabel(left_frame, text="Steganography Encoder", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(10, 20))
        
        img_label = ctk.CTkLabel(left_frame, text="Select Cover Image (PNG):", font=ctk.CTkFont(size=14))
        img_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        image_frame = ctk.CTkFrame(left_frame)
        image_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        image_entry = ctk.CTkEntry(image_frame, textvariable=self.image_path, width=400)
        image_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            image_frame, 
            text="Browse", 
            command=self.browse_image,
            width=100,
            font=ctk.CTkFont(size=13)
        )
        browse_btn.pack(side="right")

        # Mode selection
        mode_label = ctk.CTkLabel(left_frame, text="Encoding Mode:", font=ctk.CTkFont(size=14))
        mode_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        mode_frame = ctk.CTkFrame(left_frame)
        mode_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkRadioButton(
            mode_frame, 
            text="Text Message", 
            variable=self.mode, 
            value="Message",
            font=ctk.CTkFont(size=13)
        ).pack(side="left", padx=(0, 20))
        
        ctk.CTkRadioButton(
            mode_frame, 
            text="File", 
            variable=self.mode, 
            value="File",
            font=ctk.CTkFont(size=13)
        ).pack(side="left")

        # Message input
        self.message_frame = ctk.CTkFrame(left_frame)
        self.message_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        msg_label = ctk.CTkLabel(self.message_frame, text="Enter Message:", font=ctk.CTkFont(size=14))
        msg_label.pack(anchor="w", pady=(0, 5))
        
        self.message_box = ctk.CTkTextbox(self.message_frame, height=150, font=ctk.CTkFont(size=13))
        self.message_box.pack(fill="x")

        # File selection
        self.file_frame = ctk.CTkFrame(left_frame)
        
        file_label = ctk.CTkLabel(self.file_frame, text="Select File to Hide:", font=ctk.CTkFont(size=14))
        file_label.pack(anchor="w", pady=(0, 5))
        
        file_select_frame = ctk.CTkFrame(self.file_frame)
        file_select_frame.pack(fill="x")
        
        file_entry = ctk.CTkEntry(file_select_frame, textvariable=self.file_path, width=400)
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        file_btn = ctk.CTkButton(
            file_select_frame, 
            text="Browse", 
            command=self.browse_file,
            width=100,
            font=ctk.CTkFont(size=13)
        )
        file_btn.pack(side="right")
        
        # File type label
        self.file_info = ctk.StringVar(value="No file selected")
        ctk.CTkLabel(
            self.file_frame, 
            textvariable=self.file_info, 
            font=ctk.CTkFont(size=12, slant="italic")
        ).pack(anchor="w", pady=(5, 0))
        
        # Encode button
        encode_btn = ctk.CTkButton(
            left_frame, 
            text="Encode Data", 
            command=self.encode,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2D7D46",
            hover_color="#235E35"
        )
        encode_btn.pack(pady=20, padx=15, fill="x")
        
        # Image preview
        preview_label = ctk.CTkLabel(right_frame, text="Image Preview", font=ctk.CTkFont(size=16, weight="bold"))
        preview_label.pack(pady=(10, 15))
        
        self.preview_frame = ctk.CTkFrame(right_frame, fg_color="#1A1A1A")
        self.preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="No image selected")
        self.preview_label.pack(fill="both", expand=True)
        
        # Image info
        self.image_info = ctk.StringVar(value="")
        ctk.CTkLabel(
            right_frame, 
            textvariable=self.image_info,
            font=ctk.CTkFont(size=12, slant="italic")
        ).pack(pady=(0, 10))
        
    def setup_decode_tab(self):
        left_frame = ctk.CTkFrame(self.decode_tab)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=10)
        
        right_frame = ctk.CTkFrame(self.decode_tab)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=10)
        
        # Decode controls
        title_label = ctk.CTkLabel(left_frame, text="Steganography Decoder", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(10, 20))
        
        # Image selection
        img_label = ctk.CTkLabel(left_frame, text="Select Image to Decode:", font=ctk.CTkFont(size=14))
        img_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        image_frame = ctk.CTkFrame(left_frame)
        image_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        image_entry = ctk.CTkEntry(image_frame, textvariable=self.image_path, width=400)
        image_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            image_frame, 
            text="Browse", 
            command=self.browse_image,
            width=100,
            font=ctk.CTkFont(size=13)
        )
        browse_btn.pack(side="right")
        
        output_label = ctk.CTkLabel(left_frame, text="Output will be detected automatically:", font=ctk.CTkFont(size=14))
        output_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        output_info = ctk.CTkLabel(
            left_frame, 
            text="• Text messages will be displayed in a popup\n• Files will be saved to a location of your choice",
            font=ctk.CTkFont(size=13)
        )
        output_info.pack(anchor="w", padx=25, pady=(0, 15))
        
        # Decode button
        decode_btn = ctk.CTkButton(
            left_frame, 
            text="Decode Data", 
            command=self.decode,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#7D2D5E",
            hover_color="#5E2346"
        )
        decode_btn.pack(pady=20, padx=15, fill="x")
        
        # Image preview
        preview_label = ctk.CTkLabel(right_frame, text="Image Preview", font=ctk.CTkFont(size=16, weight="bold"))
        preview_label.pack(pady=(10, 15))
        
    def update_mode_display(self, *args):
        current_mode = self.mode.get()
        
        self.message_frame.pack_forget()
        self.file_frame.pack_forget()
        
        if current_mode == "Message":
            self.message_frame.pack(fill="x", padx=15, pady=(0, 15), after=self.encode_tab.winfo_children()[0].winfo_children()[3])
        else:
            self.file_frame.pack(fill="x", padx=15, pady=(0, 15), after=self.encode_tab.winfo_children()[0].winfo_children()[3])
    
    def update_image_preview(self, *args):
        path = self.image_path.get()
        if not path or not os.path.exists(path):
            # Clear preview
            self.preview_label.configure(text="No image selected", image=None)
            self.image_info.set("")
            return
            
        try:
            # Load and resize image for preview
            img = Image.open(path)
            width, height = img.size
            
            # Calculate capacity
            max_bytes = (width * height * 3 * 2) // 8
            
            # Update image info
            self.image_info.set(f"Size: {width}x{height} pixels | Max capacity: {max_bytes/1024:.1f} KB")
            
            # Create preview
            max_width, max_height = 300, 300
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            self.preview_image = ctk.CTkImage(light_image=img, dark_image=img, 
                                             size=(img.width, img.height))
            
            self.preview_label.configure(text="", image=self.preview_image)
            
        except Exception as e:
            self.preview_label.configure(text=f"Error loading image: {str(e)}", image=None)
            self.image_info.set("")
    
    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG images", "*.png")])
        if path:
            self.image_path.set(path)
    
    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path.set(path)
            # Update file info
            name = os.path.basename(path)
            ext = os.path.splitext(path)[1]
            size = os.path.getsize(path)
            size_kb = size / 1024
            
            if size_kb < 1024:
                size_text = f"{size_kb:.1f} KB"
            else:
                size_text = f"{size_kb/1024:.2f} MB"
                
            self.file_info.set(f"File: {name} | Type: {ext[1:].upper() if ext else 'Unknown'} | Size: {size_text}")
    
    def update_status(self, message):
        self.status_text.set(message)
        self.root.update_idletasks()
    
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
                
            # Encode text with marker
            data = TEXT_TYPE + text.encode('utf-8')
        else:
            file_path = self.file_path.get()
            if not os.path.isfile(file_path):
                messagebox.showerror("Error", "Please select a valid file.")
                return
                
            try:
                # Get file extension and read file data
                _, file_ext = os.path.splitext(file_path)
                
                # Get file size for user information
                file_size = os.path.getsize(file_path)
                if file_size > 10 * 1024 * 1024:  # 10 MB warning
                    proceed = messagebox.askyesno(
                        "Large File Warning", 
                        f"The selected file is {file_size/1024/1024:.2f} MB. "
                        "Encoding large files may take time and require a large image. Continue?"
                    )
                    if not proceed:
                        return
                
                self.update_status(f"Reading file data...")
                
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                ext_bytes = file_ext.encode('utf-8')
                ext_len = len(ext_bytes)
                
                # Pack the extension length as a 2-byte integer
                ext_len_bytes = struct.pack('!H', ext_len)
                
                # Combine all parts
                data = FILE_TYPE + ext_len_bytes + ext_bytes + file_data
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {str(e)}")
                return

        # Ask where to save the encoded image
        output_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG images", "*.png")]
        )
        
        if not output_path:
            return  # User cancelled
        result_queue = queue.Queue()
        
        self.update_status("Encoding data... This may take a moment.")
        
        def encode_task():
            try:
                encode_data_to_image(image, data, output_path, compress=True)
                result_queue.put(("success", len(data), output_path))
            except Exception as e:
                # Put error in queue
                result_queue.put(("error", str(e)))
        
        encoding_thread = threading.Thread(target=encode_task, daemon=True)
        encoding_thread.start()
        
        def check_result():
            try:
                result_type, *args = result_queue.get_nowait()
                
                if result_type == "success":
                    data_size, output_path = args
                    self.encoding_complete(data_size, output_path)
                else:
                    error_message = args[0]
                    self.encoding_failed(error_message)
            except queue.Empty:
                self.root.after(100, check_result)
        
        # Start checking for results
        self.root.after(100, check_result)
    
    def encoding_complete(self, data_size, output_path):
        self.update_status("Ready")
        messagebox.showinfo(
            "Success", 
            f"Data encoded successfully!\n\n"
            f"Output image: {os.path.basename(output_path)}\n"
            f"Data size: {data_size/1024:.2f} KB"
        )
    
    def encoding_failed(self, error_message):
        self.update_status("Ready")
        messagebox.showerror("Encoding Failed", f"Error: {error_message}")
    
    def decode(self):
        image = self.image_path.get()
        if not image:
            messagebox.showerror("Error", "Please select an image.")
            return
        
        result_queue = queue.Queue()
        
        self.update_status("Decoding data... This may take a moment.")
        
        def decode_task():
            try:
                # Decode data from the image
                decoded_data = decode_data_from_image(image)
                result_queue.put(("success", decoded_data))
            except Exception as e:
                result_queue.put(("error", str(e)))
        
        decoding_thread = threading.Thread(target=decode_task, daemon=True)
        decoding_thread.start()
        
        def check_result():
            try:
                result_type, *args = result_queue.get_nowait()
                
                if result_type == "success":
                    decoded_data = args[0]
                    self.process_decoded_data(decoded_data)
                else:
                    error_message = args[0]
                    self.decoding_failed(error_message)
            except queue.Empty:
                self.root.after(100, check_result)
        self.root.after(100, check_result)
    
    def process_decoded_data(self, decoded_data):
        self.update_status("Ready")
        
        try:
            if decoded_data.startswith(TEXT_TYPE):
                text = decoded_data[len(TEXT_TYPE):].decode('utf-8', errors='replace')
                
                # Create a custom dialog for displaying the text
                self.show_text_dialog("Decoded Message", text)
                
            # Check if it's file data
            elif decoded_data.startswith(FILE_TYPE):
                file_data = decoded_data[len(FILE_TYPE):]
                
                try:
                    ext_len = struct.unpack('!H', file_data[:2])[0]
                    
                    ext = file_data[2:2+ext_len].decode('utf-8', errors='replace')
                    
                    content = file_data[2+ext_len:]
                    
                    # Ask where to save the decoded file
                    save_path = filedialog.asksaveasfilename(
                        defaultextension=ext,
                        filetypes=[("All files", "*.*")]
                    )
                    
                    if save_path:
                        # Save the decoded file
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        messagebox.showinfo(
                            "Success", 
                            f"File decoded successfully!\n\n"
                            f"Saved to: {os.path.basename(save_path)}\n"
                            f"File size: {len(content)/1024:.2f} KB"
                        )
                except (struct.error, IndexError, UnicodeDecodeError) as e:
                    messagebox.showerror("Decoding Error", f"Failed to process file data: {str(e)}")
                    self.update_status("Decoding failed")
            
            # Unknown data format fallback
            else:
                try:
                    # Decode as plain text
                    text = decoded_data.decode('utf-8', errors='replace')
                    self.show_text_dialog("Decoded Message (Legacy Format)", text)
                except UnicodeDecodeError:
                    # Ask where to save as binary
                    save_path = filedialog.asksaveasfilename(
                        title="Save decoded binary data",
                        filetypes=[("All files", "*.*")]
                    )
                    
                    if save_path:
                        with open(save_path, 'wb') as f:
                            f.write(decoded_data)
                        messagebox.showinfo(
                            "Success", 
                            f"Binary data decoded successfully!\n\n"
                            f"Saved to: {os.path.basename(save_path)}\n"
                            f"Data size: {len(decoded_data)/1024:.2f} KB"
                        )
                        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process decoded data: {str(e)}")
            self.update_status("Processing failed")
    
    def decoding_failed(self, error_message):
        self.update_status("Ready")
        messagebox.showerror("Decoding Failed", f"Error: {error_message}")
    
    def show_text_dialog(self, title, text):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame, 
            text="Decoded Text Message:", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 10), anchor="w")
        
        text_container = ctk.CTkFrame(frame)
        text_container.pack(fill="both", expand=True, pady=(0, 15))
        
        text_box = ctk.CTkTextbox(text_container, font=ctk.CTkFont(size=14))
        text_box.pack(fill="both", expand=True, padx=5, pady=5)
        text_box.insert("0.0", text)
        text_box.configure(state="disabled")
        
        button_frame = ctk.CTkFrame(frame, height=50)
        button_frame.pack(fill="x")
        button_frame.pack_propagate(False)
        
        # Close button
        ctk.CTkButton(
            button_frame, 
            text="Close", 
            command=dialog.destroy,
            width=100,
            height=32,
            font=ctk.CTkFont(size=14)
        ).pack(pady=10, anchor="center")
