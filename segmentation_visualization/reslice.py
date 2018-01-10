# -*- coding: utf-8 -*-

"""Relicing functions and classes

"""
import numpy as np
from scipy.ndimage.interpolation import map_coordinates


class Reslicer:
    """Reslice a NIfTI image

    This class uses the affine matrix provided by nibabel to transfrom the image
    to physical coordinate (LPI- as base coordinate). It can currently bring
    the image to axial, coronal, and sagittal views.

    Args:
        image_array (3D numpy array): The image data read from nibabel
        order (int): The interpolation order (0 for nearest interpolation, 1 for
            linear interpolation, etc.)
        _LPI_minus_affine (4x4 numpy 2D array): The affine matrix provided by
            nibabel transforming the image into LPI- coornidate

    """

    def __init__(self, image_array, LPI_minus_affine, order=1):
        """
        Args:
            image_array (3D num_array): The image data read from nibabel
            LPI_minus_affine (4x4 numpy 2D array): The affine matrix provided by
                nibabel transforming the image into LPI- coornidate
            order (int, optional): The interpolation order (0 for nearest
                interpolation, 1 for linear interpolation, etc.)

        Raises:
            RuntimeError: If `image_array` is not 3D
            RuntimeError: If `LPI_minuxis` not 3D affine (4 x 4 homogeneous
                matrix)

        """
        assert len(image_array.shape) == 3 # 3d data
        assert np.array_equal(LPI_minus_affine.shape, (4, 4)) # homogeneous

        self.image_array = image_array
        self._LPI_minus_affine = LPI_minus_affine
        self.order = order

    def to_LPI_minus(self):
        """Transform `image_array` to LPI-

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        return self._reslice(self.image_array, self._LPI_minus_affine)

    def to_RAI_minus(self):
        """Transform `image_array` to RAI-

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        LPI_to_RAI_affine = np.array([[-1, 0, 0, 0],
                                      [0, -1, 0, 0],
                                      [0, 0, 1, 0],
                                      [0, 0, 0, 1]])
        affine = LPI_to_RAI_affine.dot(self._LPI_minus_affine)
        return self._reslice(self.image_array, affine)

    def to_RSA_minus(self):
        """Transform `image_array` to RSA-

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        LPI_to_RSA_affine = np.array([[-1, 0, 0, 0],
                                      [0, 0, -1, 0],
                                      [0, -1, 0, 0],
                                      [0, 0, 0, 1]])
        affine = LPI_to_RSA_affine.dot(self._LPI_minus_affine)
        return self._reslice(self.image_array, affine)

    def to_ASR_minus(self):
        """Transform `image_array` to ASR-

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        LPI_to_ASR_affine = np.array([[0, -1, 0, 0],
                                      [0, 0, -1, 0],
                                      [-1, 0, 0, 0],
                                      [0, 0, 0, 1]])
        affine = LPI_to_ASR_affine.dot(self._LPI_minus_affine)
        return self._reslice(self.image_array, affine)

    def to_view(self, view):
        """Transfrom `image_array` to a specific view

        Args:
            view (str): View orientation {'axial', 'coronal', 'sagittal'}

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        if view == 'axial':
            return self.to_axial()
        if view == 'coronal':
            return self.to_coronal()
        if view == 'sagittal':
            return self.to_sagittal()

    def to_axial(self):
        """Transfrom `image_array` to the axial view

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        return self.to_RAI_minus()

    def to_coronal(self):
        """Transfrom `image_array` to the coronal view

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        return self.to_RSA_minus()

    def to_sagittal(self):
        """Transfrom `image_array` to the sagittal view

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        return self.to_ASR_minus()

    def _reslice(self, image, affine):
        """Reslice an image using an affine transformation

        Args:
            image (3D numpy array): The image to transform
            affine (4 x 4 numpy matrix): The affine transform in homogeneous
                coordinate

        Returns:
            resliced_image (3D numpy array): Transfromd image
        
        """
        result_range = self._calc_scanner_coords_range(image.shape, affine)
        result = self._transform_image(image, result_range, affine) 
        return result

    def _calc_scanner_coords_range(self, image_shape, affine_vox_to_scanner):
        """Calculate the range of coordinate after transform

        The method uses the range of the image before the transform and the
        affine to calculate the range after the transform.

        Args:
            image_shape (3 x 1 numpy array): The shape of the image to transform
            affine_vox_to_scanner (4 x 4 numpy matrix): The affine to perform

        Returns:
            min_scanner_coords (3 x 1 numpy array): The lower bound of the range
                along each axis
            max_scanner_coords (3 x 1 numpy array): The upper bound of the range
                along each axis

        """
        mesh = np.meshgrid(*[(0, dim-1) for dim in image_shape])
        voxel_coords = self._stack_coords(mesh) 
        scanner_coords = affine_vox_to_scanner.dot(voxel_coords.T)
        min_scanner_coords = np.min(scanner_coords, axis=1)[:3] # [x, y, z]
        max_scanner_coords = np.max(scanner_coords, axis=1)[:3] # [x, y, z]
        return min_scanner_coords, max_scanner_coords

    def _stack_coords(self, mesh, convert_to_homogeneous=True):
        """Stack matrix of x, y, [z] coornidates together

        The method first flattens x, y, [z] matrices then stack the three 1D
        array to form a matrix of coordinates where each column represents a
        point.

        Args:
            mesh (n x n x 3(2) meshgrid): The output of meshgrid. Each n x n
                slice contains the coorindates along this direction (x, y, z)
            convert_to_homogeneous (bool): Add a row of ones to bring the
                coordinates into homogeneous coordinate

        Returns:
            coords (4(3) x num_points numpy array): The stacked meshgrid points.
                Each column represents a point
        
        """
        coords = np.hstack([m.flatten()[..., None] for m in mesh]) 
        if convert_to_homogeneous:
            coords = np.hstack([coords, np.ones((coords.shape[0], 1))])
        return coords

    def _transform_image(self, source_image, target_range, affine_s2t):
        """Transfrom an image using affine

        The method first transfroms the source image using the affine then
        translate it to the target range. For example, assume the image has
        shape 10x10x10. After the affine, the image is transformed to an image
        whose coordinates spanning as [-5, 5], [-5, 5], [-5, 5]. Suppose the
        target range is [1, 9], [2, 10], [1, 8], then the image will be further
        translated to this target range and data outside the range is thrown
        away.

        Args:
            source_image (numpy array): The image to transform
            targe_range (list of range along x, y, [z]): The final range of the 
                result image
            affine_s2t (numpy matrix): Affine matrix from source to target in 
                homogeneous coordinate

        Returns:
            target_image (numpy array): Transformed image

        """
        # Note that the affine should be applied to the points of the target
        # image therefore all affines are inverted and the order of affines are
        # reversed
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
        """Convert a translation into homogeneous coordinate

        Args:
            translation (3 x 1 numpy array): 3D translation

        Returns:
            result (4 x 1 numpy array): 3D Translation in homogeneous coordinate

        """
        dim = translation.size
        translation = np.reshape(translation, [dim, 1])
        result = np.vstack([np.hstack([np.eye(dim), translation]),
                            np.hstack([np.zeros([1, dim]), np.ones([1, 1])])])
        return result