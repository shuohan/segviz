import nibabel as nib

MAX_VAL = 255

class Overlay:

    """
    Generates a slice of the label volume on top of the image (3D) using alpha
    composition. The alpha value and the slice index can be updated
    interactively
    """

    def __init__(self, image, initial_sliceid=0, initial_alpha=0.5, **kwargs):
        """
        - kwargs: 
        > "labels": the label volume, the value at each pixel is the
          index referring to "colors".
        > "colors": colormap of the label volume, num_colors x 3 (or 4 for an
          alpha channel) RGB array
        """
        assert image.dtype == np.uint8
        self._sliceid = int(initial_sliceid)
        self._image = image
        self._min_sliceid = 0
        self._max_sliceid = self._image.shape[2] - 1
        # alpha of the label volume; alpha for the image is (1 - self._alpha)
        self._alpha = initial_alpha 
        self._alpha_step = 0.05
        self._size = (image.shape[1], image.shape[0])
        self._ratio = self._size[0] / self._size[1]
        if 'labels' in kwargs and 'colors' in kwargs:
            labels = kwargs['labels']
            colors = kwargs['colors']
            assert labels.dtype == np.int32
            assert colors.dtype == np.uint8
            self._labels = labels
            self._colors = colors
            print(self._colors.shape)
        self._overlay_pil = None
        self._update() # produce overlay_pil

    def _update(self):
        if hasattr(self, '_labels') and hasattr(self, '_colors'):
            self._overlay_pil = self._compose()
        else:
            self._overlay_pil = self._create_image_pil()
        self._overlay_pil = self._overlay_pil.resize(self._size, Image.BILINEAR)

    def resize(self, width, height):
        # keep ratio (width / height) unchanged
        ratio = width / height
        if ratio > self._ratio:
            width = height * self._ratio
        if ratio < self._ratio:
            height = width / self._ratio
        self._size = (int(width), int(height))

    def get_pil(self):
        self._update()
        return self._overlay_pil

    def get_sliceid(self):
        return self._sliceid

    def set_sliceid(self, sliceid):
        self._sliceid = max(min(sliceid, self._max_sliceid), self._min_sliceid)

    def go_to_next_slice(self):
        self._sliceid = min(self._sliceid+1, self._max_sliceid)

    def go_to_previous_slice(self):
        self._sliceid = max(self._sliceid-1, self._min_sliceid)

    def get_alpha(self):
        return self._alpha

    def set_alpha(self, alpha):
        self._alpha = max(min(alpha, 1), 0)

    def increase_alpha(self):
        self._alpha = min(self._alpha+self._alpha_step, 1)

    def decrease_alpha(self):
        self._alpha = max(self._alpha-self._alpha_step, 0)

    def to_png(self, filename):
        self._overlay_pil.save(filename, 'PNG')

    def print_label(self, x, y):
        # label = self._labels[int(x), int(y), self._sliceid]
        pass

    def print_info(self):
        print('slice: %d; alpha: %.2f' % (self._sliceid, self._alpha), end='\r')

    def _compose(self):
        pass

    def _create_image_pil(self):
        pass

        class LabelCanvas(tkinter.Label):
            def __init__(self, master, image_holder, **kwargs):
                super().__init__(master, **kwargs)
                self._image_holder = image_holder
            def update(self):
                image = self._image_holder.get_pil()
                photo = ImageTk.PhotoImage(image)
                self.configure(image=photo)
                self.image = photo
                self._image_holder.print_info()
            def go_to_previous_slice(self, event):
                self._image_holder.go_to_previous_slice()
                self.update()
            def go_to_next_slice(self, event):
                self._image_holder.go_to_next_slice()
                self.update()
            def increase_alpha(self, event):
                self._image_holder.increase_alpha()
                self.update()
            def decrease_alpha(self, event):
                self._image_holder.decrease_alpha()
                self.update()
            def focus_master(self, event):
                self.master.focus_set()
            def resize(self, event):
                self._image_holder.resize(event.width, event.height)
                self.update()
            def print_label(self, event):
                self._image_holder.print_label(event.x, event.y)
            def propagate(self, event):
                global canvases
                sliceid = self._image_holder.get_sliceid()
                for c in canvases:
                    c._image_holder.set_sliceid(sliceid)
                    c.update()

            frame.bind("<Up>", canvas.go_to_previous_slice)
            frame.bind("<Down>", canvas.go_to_next_slice)
            frame.bind("<Left>", canvas.decrease_alpha)
            frame.bind("<Right>", canvas.increase_alpha)
            frame.bind("<Return>", canvas.propagate)
            canvas.bind("<Button-1>", canvas.focus_master)
