#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import numpy as np
import nibabel as nib
from PIL import Image, ImageColor

MAX_VAL = 255

def load_image(image_path):
    image = nib.load(image_path).get_data()
    image = np.swapaxes(image, 0, 1) # transpose xy
    image = (image / np.max(image) * MAX_VAL).astype(np.uint8)
    return image

def load_labels(labels_path):
    labels = nib.load(labels_path).get_data()
    labels = np.swapaxes(labels, 0, 1)
    labels = np.round(labels).astype(np.int32)
    return labels

def get_default_colormap():
    colors = np.empty((len(ImageColor.colormap), 3), dtype=np.uint8)
    for i, (k, v) in enumerate(sorted(ImageColor.colormap.items())):
        colors[i, :] = ImageColor.getrgb(v)
    return colors

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

def concatenate_pils(all_pils):
    total_widths = list()
    max_heights = list()
    for pils in all_pils:
        widths, heights = zip(*[pil.size for pil in pils])
        total_widths.append(sum(widths))
        max_heights.append(max(heights))
    result = Image.new('RGBA', (max(total_widths), sum(max_heights)))
    x_offset = 0
    y_offset = 0
    for pils, h in zip(all_pils, max_heights):
        for pil in pils:
            size = pil.size
            print(pil, size, x_offset, y_offset)
            result.paste(pil, (x_offset, y_offset))
            x_offset += size[0]
        x_offset = 0
        y_offset += h
    return result


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='show labels on top of image')
    parser.add_argument('-p', '--input-pair', nargs='+', required=True,
                        metavar=('IMAGE', 'LABEL_VOLUME'), action='append',
                        help='image and label_volume pair; label_volume is '
                             'optional. Multiple pairs are acceptable')
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
                        type=int, required=False, nargs='+')
    parser.add_argument('-min', help='min cutoff value of image, in uint8',
                        type=int, default=0, required=False)
    parser.add_argument('-max', help='max cutoff value of image, in uint8',
                        type=int, default=MAX_VAL, required=False)
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
    parser.add_argument('-o', '--output-filename', type=str, required=False,
                        default=None)
    parser.add_argument('-ori', '--orientation', required=False, default=None)
    args = parser.parse_args()

    print(args)

    print(args.output_filename)

    if args.colors is not None:
        colors = load_colors(args.colors)

    overlays = list()
    sliceid = args.sliceid
    for sid in sliceid:
        overlay_slices = list()
        for i, pair_paths in enumerate(args.input_pair):
            im_dirname, im_basename = os.path.split(pair_paths[0])
            obj = nib.load(pair_paths[0])
            res = np.min(obj.header.get_zooms())
            tmp_im_filename = os.path.join(im_dirname,
                                           'reorient_'+str(i)+im_basename)
            command = '3dresample -orient %s -prefix %s -input %s -dxyz %.2f %.2f %.2f'
            command = command % (args.orientation, tmp_im_filename, pair_paths[0],
                                 res, res, res)
            os.system(command)
            image = load_image(tmp_im_filename)
            image = rescale_image(image, args.min, args.max)
            os.system('rm -f '+tmp_im_filename)
            # if args.sliceid is None:
            #     sliceid = [int(image.shape[2] / 2)]
            # else:
            #     sliceid = args.sliceid
            if len(pair_paths) > 1:
                lab_dirname, lab_basename = os.path.split(pair_paths[1])
                tmp_lab_filename = os.path.join(lab_dirname,
                                                'reorient_'+str(i)+lab_basename)
                command = '3dresample -orient %s -rmode NN -prefix %s -input %s -dxyz %.2f %.2f %.2f'
                command = command % (args.orientation, tmp_lab_filename,
                                     pair_paths[1], res, res, res)
                os.system(command)
                labels = load_labels(tmp_lab_filename)
                os.system('rm -f '+tmp_lab_filename)
                if args.convert_colors:
                    converted_colors = convert_colors(colors, labels)
                    print(converted_colors.shape)
                overlay = Overlay(image, sid, args.alpha, labels=labels,
                                  colors=converted_colors)
            else:
                overlay = Overlay(image, sliceid, args.alpha)
            overlay_slices.append(overlay)
        overlays.append(overlay_slices)

    if not args.interactive:
        pils = list()
        for overlay_slices in overlays:
            pils.append([overlay.get_pil() for overlay in overlay_slices])
        montage = concatenate_pils(pils)
        if args.output_filename is None:
            montage.show()
        else:
            print('saving')
            montage.save(args.output_filename, 'PNG')

    else:

        overlays = overlays[0]

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

        root = tkinter.Tk()
        root.geometry('500x500')
        canvases = list()
        for overlay in overlays:
            frame = tkinter.Frame(root)
            frame.pack(fill=tkinter.BOTH, expand=tkinter.YES, side=tkinter.LEFT)
            canvas = LabelCanvas(frame, overlay)
            canvas.pack(fill=tkinter.BOTH, expand=tkinter.YES)
            canvas.update()
            canvases.append(canvas)
            frame.bind("<Up>", canvas.go_to_previous_slice)
            frame.bind("<Down>", canvas.go_to_next_slice)
            frame.bind("<Left>", canvas.decrease_alpha)
            frame.bind("<Right>", canvas.increase_alpha)
            frame.bind("<Return>", canvas.propagate)
            # frame.bind("<Configure>", canvas.resize)
            canvas.bind("<Button-1>", canvas.focus_master)
        root.mainloop()
