import numpy as np
from scipy.ndimage.interpolation import map_coordinates


class Reslicer:

    def __init__(self, image_array, LPI_minus_affine, order=1):

        # LPI_minus_affine: homogeneous affine matrix from voxel coordinates to
        # scanner coordinates; 4x4 matrix; x: left(-) -> right(+), y:
        # posterior(-) -> anterior(+), z: interior(-) -> posterior(+); this 
        # is nibabel's default affine

        assert len(image_array.shape) == 3 # 3d data
        assert np.array_equal(LPI_minus_affine.shape, (4, 4)) # homogeneous

        self.image_array = image_array
        self._LPI_minus_affine = LPI_minus_affine
        self.order = order

    def to_LPI_minus(self):
        return self._reslice(self.image_array, self._LPI_minus_affine)

    def to_RAI_minus(self):
        LPI_to_RAI_affine = np.array([[-1, 0, 0, 0],
                                      [0, -1, 0, 0],
                                      [0, 0, 1, 0],
                                      [0, 0, 0, 1]])
        affine = LPI_to_RAI_affine.dot(self._LPI_minus_affine)
        return self._reslice(self.image_array, affine)

    def to_RSA_minus(self):
        LPI_to_RSA_affine = np.array([[-1, 0, 0, 0],
                                      [0, 0, -1, 0],
                                      [0, -1, 0, 0],
                                      [0, 0, 0, 1]])
        affine = LPI_to_RSA_affine.dot(self._LPI_minus_affine)
        return self._reslice(self.image_array, affine)

    def to_ASR_minus(self):
        LPI_to_ASR_affine = np.array([[0, -1, 0, 0],
                                      [0, 0, -1, 0],
                                      [-1, 0, 0, 0],
                                      [0, 0, 0, 1]])
        affine = LPI_to_ASR_affine.dot(self._LPI_minus_affine)
        return self._reslice(self.image_array, affine)

    def to_view(self, view):
        # view: 'axial', 'coronal', 'sagittal'
        if view == 'axial':
            return self.to_axial()
        if view == 'coronal':
            return self.to_coronal()
        if view == 'sagittal':
            return self.to_sagittal()

    def to_axial(self):
        return self.to_RAI_minus()

    def to_coronal(self):
        return self.to_RSA_minus()

    def to_sagittal(self):
        return self.to_ASR_minus()

    def _reslice(self, image, affine):
        result_range = self._calc_scanner_coords_range(image.shape, affine)
        result = self._transform_image(image, result_range, affine) 
        return result

    def _calc_scanner_coords_range(self, image_shape, affine_vox_to_scanner):
        mesh = np.meshgrid(*[(0, dim-1) for dim in image_shape])
        voxel_coords = self._stack_coords(mesh) 
        scanner_coords = affine_vox_to_scanner.dot(voxel_coords.T)
        min_scanner_coords = np.min(scanner_coords, axis=1)[:3] # [x, y, z]
        max_scanner_coords = np.max(scanner_coords, axis=1)[:3] # [x, y, z]
        return min_scanner_coords, max_scanner_coords

    def _stack_coords(self, mesh, convert_to_homogeneous=True):
        coords = np.hstack([m.flatten()[..., None] for m in mesh]) 
        if convert_to_homogeneous:
            coords = np.hstack([coords, np.ones((coords.shape[0], 1))])
        return coords

    def _transform_image(self, source_image, target_range, affine_s2t):
        # center target_image_coords such that min_range -> [0, 0, 0]
        offset = self._convert_translation_to_homogeneous(target_range[0])
        affine_t2s = np.linalg.inv(affine_s2t).dot(offset)
        target_shape = np.ceil(target_range[1]-target_range[0]+1).astype(int)
        mesh = np.meshgrid(*[np.arange(dim) for dim in target_shape])
        target_coords = self._stack_coords(mesh)
        source_coords = affine_t2s.dot(target_coords.T)
        target_tmp = map_coordinates(source_image, source_coords[:3, :],
                                     order=self.order)
        target_image = np.reshape(target_tmp, mesh[0].shape)
        return target_image

    def _convert_translation_to_homogeneous(self, translation):
        dim = translation.size
        translation = np.reshape(translation, [dim, 1])
        result = np.vstack([np.hstack([np.eye(dim), translation]),
                            np.hstack([np.zeros([1, dim]), np.ones([1, 1])])])
        return result
