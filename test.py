#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import numpy as np
import nibabel as nib
from PIL import Image, ImageColor

MAX_VAL = 255

def load_image(image_path):
    image = nib.load(args.image).get_data()
    image = np.swapaxes(image, 0, 1) # transpose xy
    image = (image / np.max(image) * MAX_VAL).astype(np.uint8)
    return image

def rescale_image(image, min_val, max_val):
    # image, min_val, max_val in uint8
    # a x old_val + b = new_val
    b = min_val
    a = float(max_val - min_val) / MAX_VAL
    image = (a * image + b).astype(np.uint8)
    return image

def load_labels(labels_path):
    labels = nib.load(args.labels).get_data()
    labels = np.swapaxes(labels, 0, 1)
    labels = np.round(labels).astype(np.int32)
    return labels

def load_colors(colors_path):
    # the first row is the background color
    if not os.path.isfile(colors_path):
        print('File', colors_path, 'does not exist. Using default colormap')
        colors = get_default_colormap()
    else: 
        colors = np.load(colors_path)
        colors = (MAX_VAL * colors).astype(np.uint8)
    if colors.shape[1] < 4: # no alpha channel
        alphas = MAX_VAL * np.ones((colors.shape[0], 1), dtype=np.uint8)
        colors = np.hstack([colors, alphas])
    colors[0, 3] = 0 # background alpha is 0
    return colors

def get_default_colormap():
    colors = np.empty((len(ImageColor.colormap), 3), dtype=np.uint8)
    for i, (k, v) in enumerate(sorted(ImageColor.colormap.items())):
        colors[i, :] = ImageColor.getrgb(v)
    return colors

def convert_colors(colors, labels):
    label_set = np.unique(labels)
    new_colors_shape = (np.max(label_set)+1, colors.shape[1])
    new_colors = np.empty(new_colors_shape, dtype=np.uint8)
    indices = np.mod(np.arange(len(label_set), dtype=int), colors.shape[0])
    new_colors[label_set, :] = colors[indices, :]
    return new_colors


class Overlay:

    def __init__(self, image, initial_sliceid=0, initial_alpha=0.5, **kwargs):
        assert image.dtype == np.uint8
        self._sliceid = int(initial_sliceid)
        self._image = image
        self._min_sliceid = 0
        self._max_sliceid = self._image.shape[2] - 1
        self._alpha = initial_alpha
        self._alpha_step = 0.05
        self._size = (image.shape[0], image.shape[1])
        self._ratio = self._size[0] / self._size[1]
        if 'labels' in kwargs and 'colors' in kwargs:
            assert labels.dtype == np.int32
            assert colors.dtype == np.uint8
            self._labels = labels
            self._colors = colors
        self._overlay_pil = None
        self._update() # produce overlay_pil

    def _update(self):
        if hasattr(self, '_labels') and hasattr(self, '_colors'):
            self._overlay_pil = self._compose()
        else:
            self._overlay_pil = self._create_image_pil()
        self._overlay_pil = self._overlay_pil.resize(self._size, Image.BILINEAR)

    def resize(self, width, height):
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
        image_pil = self._create_image_pil()
        labels_slice = self._colors[self._labels[:, :, self._sliceid], :]
        labels_slice[:, :, 3] = labels_slice[:, :, 3] * self._alpha
        labels_pil = Image.fromarray(labels_slice).convert('RGBA')
        overlay_pil = Image.alpha_composite(image_pil, labels_pil)
        return overlay_pil

    def _create_image_pil(self):
        image_slice = self._image[:, :, self._sliceid]
        image_slice = np.repeat(image_slice[:, :, None], 3, 2)
        image_pil = Image.fromarray(image_slice).convert('RGBA')
        return image_pil


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='show labels on top of image')
    parser.add_argument('image')
    parser.add_argument('-l', '--labels', required=False, default=None)
    parser.add_argument('-c', '--colors', default=None, required=False,
                        help='a numpy file containing the colors of labels; '
                             'the loaded colors should be a num_colors x 3 '
                             'array whose columns are R, G, B; the order of '
                             'the rows corresponds to the ascent of label '
                             'values (check -r for more details; the first '
                             'label value (normally 0) corresponds to the '
                             'background whose color alpha will be set to 0 '
                             'during visualization')
    parser.add_argument('-a', '--alpha', help='transparency of the label image',
                        default=0.5, required=False, type=float)
    parser.add_argument('-n', '--sliceid', help='slice no.', default=None,
                        type=int, required=False)
    parser.add_argument('-min', help='min cutoff value of image, in uint8',
                        type=np.uint8, default=0, required=False)
    parser.add_argument('-max', help='max cutoff value of image, in uint8',
                        type=np.uint8, default=MAX_VAL, required=False)
    parser.add_argument('-r', '--convert_colors', action='store_true',
                        help='by default, the value of a label is directly the '
                             'index of a color; in case the colors is only '
                             'stored in the order of the ascent of the label '
                             'values (for example, labels are 2, 5, 10, but '
                             'there are only three colors, we need to convert '
                             '2, 5, 10 to 0, 1, 2), use this option to create '
                             'a index "reference", then the color is get via '
                             'colors[ref[label_val]]', default=False)
    parser.add_argument('-i', '--interactive', action='store_true', 
                        default=False, help='use gui to navigate image',
                        required=False)
    args = parser.parse_args()

    image = load_image(args.image)
    image = rescale_image(image, args.min, args.max)
    if args.sliceid is None:
        args.sliceid = int(image.shape[2] / 2) 

    if args.labels is not None:
        labels = load_labels(args.labels)
        colors = load_colors(args.colors)
        if args.convert_colors:
            colors = convert_colors(colors, labels)
        overlay = Overlay(image, args.sliceid, args.alpha, labels=labels,
                          colors=colors)
    else:
        overlay = Overlay(image, args.sliceid, args.alpha)

    if not args.interactive:
        overlay.get_pil().show()

    else:

        import tkinter
        from PIL import ImageTk

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
            def go_to_previous_slice(self):
                self._image_holder.go_to_previous_slice()
                self.update()
            def go_to_next_slice(self):
                self._image_holder.go_to_next_slice()
                self.update()
            def increase_alpha(self):
                self._image_holder.increase_alpha()
                self.update()
            def decrease_alpha(self):
                self._image_holder.decrease_alpha()
                self.update()
            def resize(self, event):
                self._image_holder.resize(event.width, event.height)
                self.update()
            def print_label(self, event):
                self._image_holder.print_label(event.x, event.y)

        root = tkinter.Tk()
        canvas = LabelCanvas(root, overlay)
        root.bind("<Up>", lambda event: canvas.go_to_previous_slice())
        root.bind("<Down>", lambda event: canvas.go_to_next_slice())
        root.bind("<Left>", lambda event: canvas.decrease_alpha())
        root.bind("<Right>", lambda event: canvas.increase_alpha())
        root.bind("<Configure>", lambda event: canvas.resize(event))
        root.bind("<Button 1>", lambda event: canvas.print_label(event))
        root.geometry('500x500')
        canvas.place(x=0,y=0)
        canvas.pack(fill=tkinter.BOTH, expand=tkinter.YES)
        canvas.update()
        root.mainloop()
