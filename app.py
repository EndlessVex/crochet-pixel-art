import tkinter as tk
from tkinter import filedialog, Label, Button, messagebox, Scale, HORIZONTAL, Frame, Checkbutton, IntVar
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import math
from collections import Counter

class PixelArtApp:
    def __init__(self, root):
        # Setting up the window
        self.root = root
        self.root.title("Pixel Art Maker")
        self.current_color_idx = None

        # Making the upload and paste image buttons
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.upload_btn = Button(button_frame, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(side="left", padx=5)

        self.paste_btn = Button(button_frame, text="Paste Image", command=self.paste_image)
        self.paste_btn.pack(side="left", padx=5)

        # Slider for pixelation control
        pixel_slider_frame = Frame(self.root)
        pixel_slider_frame.pack(pady=10)

        pixel_slider_label = Label(pixel_slider_frame, text="Pixelation Level:")
        pixel_slider_label.grid(row=0, column=0, sticky="e", padx=(0, 5))

        self.pixel_slider = Scale(pixel_slider_frame, from_=2, to=100, orient=HORIZONTAL, command=self.update_pixelation)
        self.pixel_slider.set(10)
        self.pixel_slider.grid(row=0, column=1)

        # Slider for number of colors
        color_select_frame = Frame(self.root)
        color_select_frame.pack(pady=10)

        color_count_label = Label(color_select_frame, text="Number of Colors:")
        color_count_label.grid(row=0, column=0, sticky="e", padx=(0, 5))

        self.color_count_slider = Scale(color_select_frame, from_=2, to=18, orient=HORIZONTAL, command=self.create_color_boxes)
        self.color_count_slider.set(3)
        self.color_count_slider.grid(row=0, column=1)

        # Button to auto select colors
        self.auto_color_btn = Button(color_select_frame, text="Auto Select Colors", command=self.auto_select_colors)
        self.auto_color_btn.grid(row=0, column=2, padx=(10, 0))

        # Frame for color boxes
        self.color_box_frame = Frame(root)
        self.color_box_frame.pack(pady=10)

        self.color_boxes = []

        # Button to apply the selected colors
        self.apply_colors_btn = Button(root, text="Apply Colors", command=self.apply_selected_colors)
        self.apply_colors_btn.pack(pady=10)

        # Button to grid and upscale the image
        self.upscale_btn = Button(root, text="Upscale and Grid", command=self.upscale_and_grid)
        self.upscale_btn.pack(pady=10)

        # Image display
        self.canvas_label = Label(root)
        self.canvas_label.pack(pady=10)

        # Vars
        self.original_image = None
        self.pixelated_image = None
        self.preview_size = None

    # Upload image from a file
    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            img = Image.open(file_path).convert('RGBA')
            self.original_image = self.remove_transparency(img)
            self.pixelate_and_display(first_load=True)

    # Paste image from clipboard
    def paste_image(self):
        try:
            clipboard_img = ImageGrab.grabclipboard()
            if isinstance(clipboard_img, Image.Image):
                img = clipboard_img.convert('RGBA')
                self.original_image = self.remove_transparency(img)
                self.pixelate_and_display(first_load=True)
            else:
                messagebox.showerror("Paste Error", "Clipboard aint got not image.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # Remove any transparency from the image and replace it with white
    def remove_transparency(self, im, bg_colour=(255, 255, 255)):
        if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
            alpha = im.convert('RGBA').split()[-1]
            bg = Image.new("RGBA", im.size, bg_colour + (255,))
            bg.paste(im, mask=alpha)
            return bg.convert('RGB')
        else:
            return im.convert('RGB')

    # Update the pixelation on the display
    def update_pixelation(self, event=None):
            if self.original_image:
                self.pixelate_and_display(first_load=False)

    # Pixelate the image and display preview
    def pixelate_and_display(self, first_load=False):
        pixel_size = self.pixel_slider.get()
        img_small = self.original_image.resize(
            (max(1, self.original_image.width // pixel_size), max(1, self.original_image.height // pixel_size)),
            resample=Image.BILINEAR
        )
        self.pixelated_image = img_small.resize(
            (self.original_image.width, self.original_image.height),
            Image.NEAREST
        )

        if first_load:
            preview_img = self.pixelated_image.copy()
            preview_img.thumbnail((800, 800), Image.LANCZOS)
            self.preview_size = preview_img.size

            self.tkimg = ImageTk.PhotoImage(preview_img)
            self.canvas_label.config(image=self.tkimg)

            self.root.update_idletasks()
            extra_ui_height = 220

            window_width = self.preview_size[0]
            window_height = self.preview_size[1] + extra_ui_height
            self.root.geometry(f"{window_width}x{window_height}")

        else:
            preview_img = self.pixelated_image.copy().resize(self.preview_size, Image.LANCZOS)
            self.tkimg = ImageTk.PhotoImage(preview_img)
            self.canvas_label.config(image=self.tkimg)

    # Creates the color selection boxes
    def create_color_boxes(self, event=None):
        existing_colors = [box["color"] for box in self.color_boxes]
        
        for widget in self.color_box_frame.winfo_children():
            widget.destroy()

        self.color_boxes = []
        color_count = self.color_count_slider.get()

        max_columns = 6
        for i in range(color_count):
            color = existing_colors[i] if i < len(existing_colors) else None
            bg_color = '#%02x%02x%02x' % color if color else "white"

            box = Label(self.color_box_frame, text=f"Color {i+1}", bg=bg_color, width=10, height=2, relief="ridge", borderwidth=2)
            box.grid(row=i // max_columns, column=i % max_columns, padx=5, pady=5)
            box.bind("<Button-1>", lambda e, idx=i: self.select_color(idx))
            
            self.color_boxes.append({"widget": box, "color": color})

    # Elects color from image using eyedropper
    def select_color(self, idx):
        self.current_color_idx = idx

        self.canvas_label.config(cursor="crosshair")

        self.canvas_label.bind("<Motion>", self.preview_color_from_image)
        self.canvas_label.bind("<Button-1>", self.confirm_color_from_image)

    # Previews the color you are eyedropping
    def preview_color_from_image(self, event):
        label_width = self.canvas_label.winfo_width()
        label_height = self.canvas_label.winfo_height()

        img_width, img_height = self.preview_size

        offset_x = (label_width - img_width) // 2
        offset_y = (label_height - img_height) // 2

        x, y = event.x - offset_x, event.y - offset_y

        if (0 <= x < img_width) and (0 <= y < img_height):
            img_x = int(x * self.pixelated_image.width / img_width)
            img_y = int(y * self.pixelated_image.height / img_height)

            picked_color = self.pixelated_image.getpixel((img_x, img_y))
            hex_color = '#%02x%02x%02x' % picked_color[:3]

            box = self.color_boxes[self.current_color_idx]["widget"]
            box.config(bg=hex_color)

    # Confirms color selection
    def confirm_color_from_image(self, event):
        label_width = self.canvas_label.winfo_width()
        label_height = self.canvas_label.winfo_height()

        img_width, img_height = self.preview_size

        offset_x = (label_width - img_width) // 2
        offset_y = (label_height - img_height) // 2

        x, y = event.x - offset_x, event.y - offset_y

        if (0 <= x < img_width) and (0 <= y < img_height):
            img_x = int(x * self.pixelated_image.width / img_width)
            img_y = int(y * self.pixelated_image.height / img_height)

            picked_color = self.pixelated_image.getpixel((img_x, img_y))
            hex_color = '#%02x%02x%02x' % picked_color[:3]

            box = self.color_boxes[self.current_color_idx]["widget"]
            box.config(bg=hex_color)
            self.color_boxes[self.current_color_idx]["color"] = picked_color[:3]

        self.canvas_label.unbind("<Motion>")
        self.canvas_label.unbind("<Button-1>")
        self.canvas_label.config(cursor="")

    # Apply the selected colors
    def apply_selected_colors(self):
        selected_colors = [box["color"] for box in self.color_boxes if box["color"]]

        if not selected_colors:
            messagebox.showerror("No Colors Selected", "Please select colors before applying.")
            return
        
        color_distance_threshold = 100
        
        img = self.pixelated_image.copy().convert('RGB')
        pixels = img.load()

        width, height = img.size

        for y in range(height):
            for x in range(width):
                current_color = pixels[x, y]
                closest_color, closest_distance = min(
                    ((c, self.color_distance(c, current_color)) for c in selected_colors),
                    key=lambda item: item[1]
                )

                if closest_distance > color_distance_threshold:
                    pixels[x, y] = (255, 255, 255)
                else:
                    pixels[x, y] = closest_color

        self.pixelated_image = img

        preview_img = self.pixelated_image.copy().resize(self.preview_size, Image.NEAREST)
        self.tkimg = ImageTk.PhotoImage(preview_img)
        self.canvas_label.config(image=self.tkimg)


    # Auto select the colors from the image based on number of color boxes
    def auto_select_colors(self):
        if self.original_image is None:
            messagebox.showerror("No Image", "Upload or paste an image first.")
            return

        color_count = self.color_count_slider.get()

        palette_img = self.original_image.convert("P", palette=Image.ADAPTIVE, colors=color_count)
        palette = palette_img.getpalette()
        color_counts = sorted(palette_img.getcolors(), reverse=True)

        palette_colors = []
        seen_colors = set()
        for count, idx in color_counts:
            color = tuple(palette[idx*3:idx*3+3])
            if color not in seen_colors:
                palette_colors.append(color)
                seen_colors.add(color)
            if len(palette_colors) == color_count:
                break

        for widget in self.color_box_frame.winfo_children():
            widget.destroy()

        self.color_boxes = []
        max_columns = 6
        for i, color in enumerate(palette_colors):
            hex_color = '#%02x%02x%02x' % color
            box = Label(self.color_box_frame, text=f"Color {i+1}", bg=hex_color, width=10, height=2, relief="ridge", borderwidth=2)
            box.grid(row=i // max_columns, column=i % max_columns, padx=5, pady=5)
            box.bind("<Button-1>", lambda e, idx=i: self.select_color(idx))
            self.color_boxes.append({"widget": box, "color": color})

    # Upscale the pixelated image and apply grid
    def upscale_and_grid(self, scale_factor=10, grid_color=(200, 200, 200)):
        if self.pixelated_image is None:
            messagebox.showerror("No Image", "Please pixelate and apply colors first.")
            return
        
        orig_pixel_width = max(1, self.original_image.width // self.pixel_slider.get())
        orig_pixel_height = max(1, self.original_image.height // self.pixel_slider.get())

        img_small = self.pixelated_image.resize(
            (orig_pixel_width, orig_pixel_height),
            resample=Image.NEAREST
        )

        upscaled_img = img_small.resize(
            (orig_pixel_width * scale_factor, orig_pixel_height * scale_factor),
            Image.NEAREST
        )

        draw = ImageDraw.Draw(upscaled_img)

        for x in range(0, upscaled_img.width + 1, scale_factor):
            draw.line((x, 0, x, upscaled_img.height), fill=grid_color)
        
        for y in range(0, upscaled_img.height + 1, scale_factor):
            draw.line((0, y, upscaled_img.width, y), fill=grid_color)

        self.show_final_image(upscaled_img)

    # Display final image in new window
    def show_final_image(self, img):
        final_window = tk.Toplevel(self.root)
        final_window.title("Upscaled Pixel Art with Grid")

        preview = img.copy()
        preview.thumbnail((800, 800), Image.LANCZOS)
        tkimg_final = ImageTk.PhotoImage(preview)

        label = Label(final_window, image=tkimg_final)
        label.image = tkimg_final
        label.pack(pady=10)

        save_btn = Button(final_window, text="Save Image", command=lambda: self.save_image(img))
        save_btn.pack(pady=10)

    # Saves the final image
    def save_image(self, img):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
        if file_path:
            img.save(file_path)
            messagebox.showinfo("Saved", f"Image successfully saved to:\n{file_path}")

    # Calculates distance between two colors
    @staticmethod
    def color_distance(c1, c2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


if __name__ == "__main__":
    root = tk.Tk()
    app = PixelArtApp(root)
    root.mainloop()