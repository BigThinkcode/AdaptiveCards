#!/usr/bin/python

# pip install lxml
"""
Module contains functions needed for generating synthetic image dataset.
"""
import random
import os
import glob
import logging
from typing import List, Sequence, Any, Dict
import cv2
import numpy as np
from mystique import config


logger = logging.getLogger("commands.generate_bulk_data")
LOGFORMAT = "%(asctime)s - [%(filename)s:%(lineno)s - %(funcName)20s()] - \
    %(levelname)s - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOGFORMAT)


class CardElements:
    """
    This class is responsible for the card elements properties
    and its related functionalities
    The card_elements directory default path is defined in the init
    function and can also be passed as argument during runtime
    which is not compulsory
    """

    def __init__(self, number_of_elements: int, elements_dir: str) -> None:
        self.number_of_elements = number_of_elements
        self.elements_dir = elements_dir
        self.elements_with_path = self.get_elements_path()
        self.element_dimensions = self.get_elements_dimensions(
            self.elements_with_path
        )
        self.elements_type = self.get_elements_type(self.elements_with_path)
        self.attach_mandatory_element = self.get_mandatory_element(self.elements_with_path)
        self.has_merged_elements = None
        self.element_positions = None

    def get_mandatory_element(self, elements_with_path):
        """
        Replaces an mandatory element like textbox or image which is configured in
        MANDATORY_CARD_ELEMENTS to the list of elements paths.
        @param self: CardElements object
        @param elements_with_path: List of elements path
        @return elements_with_path: List of elements path
        """
        if config.MANDATORY_CARD_ELEMENTS:
            for index, mandatory_element in enumerate(config.MANDATORY_CARD_ELEMENTS):
                if any(mandatory_element in path for path in elements_with_path):
                    continue
                random_mandatory_element_path = random.sample(glob.glob(self.elements_dir + f"{mandatory_element}/*.*"),
                                                              k=1)
                elements_with_path.pop(index)
                elements_with_path.insert(index, random_mandatory_element_path[0])
        return elements_with_path

    def get_elements_path(self) -> Dict[str, str]:
        """
        Returns a list of complete path of card_elements selected at random
        @param self: CardElements object
        @return: elements_with_path
        """
        elements = glob.glob(self.elements_dir + "/**/*.*", recursive=True)
        elements_exist = [os.path.isfile(filepath) for filepath in elements]
        if elements_exist:
            elements_with_path = random.sample(
                elements, k=self.number_of_elements
            )
            elements_with_path = self.get_mandatory_element(elements_with_path)
        else:
            error_msg = "No image elements found under card_elements directory"
            logger.error(error_msg)
            raise Exception(error_msg)
        return elements_with_path

    @staticmethod
    def get_elements_type(elements_with_path: List[str]) -> Dict[int, str]:
        """
        Returns the list of element types of card_elements
        @params self: CardElements object
        @return: element_types
        """
        element_type = [os.path.basename(os.path.dirname(element)) for element in elements_with_path]
        element_type = {k: v for k, v in enumerate(element_type)}
        return element_type

    @staticmethod
    def get_elements_dimensions(elements_with_path: List[str]) -> List[tuple]:
        """
        Returns a list of dimensions for the selected elements
        @param elements_with_path : list of selected element paths
        @return : elements_dimensions
        """
        elements_dimensions = []
        for element in elements_with_path:
            element_img = cv2.imread(element)
            dimension = element_img.shape
            elements_dimensions.append(dimension)
        return elements_dimensions

    def add_padding_to_img_elements(self, elements_with_path: List[str],
                                    elements_type: Dict[int, str]) -> List[Sequence]:
        """
        Returns a list of elements in image format padded
        along width of the image
        @param elements_with_path: list of elements path from elements directory
        @param elements_type: list of element categories
        @return: reshaped_image_elements
        """
        sorted_elements_with_path = position_elements_path(elements_with_path, elements_type)

        # updating parameters necessary for annotations
        self.elements_with_path = sorted_elements_with_path
        elements_type = self.get_elements_type(self.elements_with_path)
        self.elements_type = elements_type
        updated_element_dimensions = self.get_elements_dimensions(sorted_elements_with_path)
        self.element_dimensions = updated_element_dimensions

        # selecting random element positions from the available positions for elements in config
        element_random_positions = get_random_elements_positions(elements_type)
        self.element_positions = element_random_positions
        image_elements = [cv2.imread(element) for element in sorted_elements_with_path]

        # check for element merging
        element_merge = check_possible_element_merge(element_random_positions, sorted_elements_with_path)

        reference_canvas_width = max(
            [element.shape[1] for element in image_elements]
        )

        reshaped_image_elements = []
        for e_index, image_element in enumerate(image_elements):
            image_element_width = image_element.shape[1]
            pixel_diff_width = reference_canvas_width - image_element_width
            e_position = element_random_positions[e_index]

            merge = element_merge[e_index]
            first_element_for_merging = element_merge[e_index] and\
                                        element_merge[e_index + 1 if len(image_elements)-1 != e_index else 0]
            if first_element_for_merging:
                first_image_height_with_merge = image_elements[e_index].shape[0]
                second_image_height = image_elements[e_index + 1 if len(image_elements) - 1 != e_index else 0].shape[0]
                first_image_width = image_elements[e_index].shape[1]
                second_image_width = image_elements[e_index + 1 if len(image_elements) - 1 != e_index else 0].shape[1]
                pixel_diff_height = abs(first_image_height_with_merge - second_image_height)

            if 'right' in e_position:
                top_padding_for_merge = 10
                left_padding = pixel_diff_width + 10
                if merge:
                    left_padding = 10
                    if first_image_height_with_merge > second_image_height:
                        top_padding_for_merge = pixel_diff_height + 10

                padded_image_element = cv2.copyMakeBorder(
                    image_element,
                    top=top_padding_for_merge,
                    bottom=10,
                    left=left_padding,
                    right=10,
                    borderType=cv2.BORDER_CONSTANT,
                    value=config.CANVAS_COLOR["WHITE"],
                )
            elif 'left' in e_position:
                top_padding_for_merge = 10
                right_padding = pixel_diff_width + 10
                if merge:
                    right_padding = reference_canvas_width - (first_image_width + 10 + second_image_width)
                    if first_image_height_with_merge < second_image_height:
                        top_padding_for_merge = pixel_diff_height + 10

                padded_image_element = cv2.copyMakeBorder(
                    image_element,
                    top=top_padding_for_merge,
                    bottom=10,
                    left=10,
                    right=right_padding,
                    borderType=cv2.BORDER_CONSTANT,
                    value=config.CANVAS_COLOR["WHITE"],
                )
            else:
                raise Exception('Position configuration for the elements are not provided')
            reshaped_image_elements.append(padded_image_element)

        # replacing the merged image with the existing one and adding dummy white image inplace of second image
        if any(element_merge):
            for e_index, merge in enumerate(element_merge):
                merge = element_merge[e_index] and element_merge[
                    e_index + 1 if len(image_elements) - 1 != e_index else 0]
                if merge:
                    first_img = reshaped_image_elements[e_index]
                    second_img = reshaped_image_elements[e_index + 1]
                    # second_img[:first_img.shape[0], :first_img.shape[1]] = second_img
                    merged_img = np.concatenate((first_img, second_img), axis=1)
                    dummy_img = np.ones(merged_img.shape, np.uint8) * 255
                    reshaped_image_elements.pop(e_index + 1)
                    reshaped_image_elements.pop(e_index)
                    reshaped_image_elements.insert(e_index, merged_img)
                    reshaped_image_elements.insert(e_index + 1, dummy_img)

                    # passing info for annotator
                    self.has_merged_elements = element_merge

        return reshaped_image_elements


def get_random_elements_positions(elements_type):
    random_element_positions = {}
    elements_position_key = config.ELEMENT_POSITION

    for index, element in elements_type.items():
        random_pos = random.choice(elements_position_key[element])
        random_element_positions.update({index: random_pos})
    return random_element_positions


def position_elements_path(elements_with_path, elements_type):

    elements_position_key = config.ELEMENT_POSITION
    sorted_elements_path = {'top': [], 'mid': [], 'bottom': []}
    for path_index, element_path in enumerate(elements_with_path):
        e_path_type = elements_type[path_index]
        elements_position = elements_position_key[e_path_type]
        bottom = [position for position in elements_position if 'bottom' in position]
        top = [position for position in elements_position if 'top' in position]
        mid = [position for position in elements_position if 'mid' in position]
        if top:
            sorted_elements_path.get('top').append(element_path)
        elif bottom:
            sorted_elements_path.get('bottom').append(element_path)
        elif mid:
            sorted_elements_path.get('mid').append(element_path)
        else:
            pass
    sorted_elements_path = sorted_elements_path.get('top') + sorted_elements_path.get('mid')\
                           + sorted_elements_path.get('bottom')
    return sorted_elements_path


def check_possible_element_merge(element_positions, elements_path):
    """
    Returns a list of boolean values that specify which elements are
    capable of merging
    """
    e_merge = []
    dimensions = CardElements.get_elements_dimensions(elements_path)
    canvas_width = max([dimension[1] for dimension in dimensions])
    for index, position in element_positions.items():
        if index == 0:
            e_merge.insert(index, False)
            continue

        prev_position = element_positions[index-1]
        if 'left' in prev_position and 'right' in position and prev_position.split('_')[0] == position.split('_')[0]:
            if dimensions[index][1]+dimensions[index-1][1] < canvas_width:
                e_merge.insert(index-1, True)
                e_merge.pop(index)
                e_merge.insert(index, True)
            else:
                e_merge.insert(index, False)
        else:
            e_merge.insert(index, False)

    return e_merge

def generate_image(reshaped_image_elements: List[Sequence]) -> List[Sequence]:
    """
    Stacks the image elements along an axis and return a list of them
    @param reshaped_image_elements: list of image elements after padding
    @return: stacked image elements in one or two columns respectively
    """
    number_of_elements = len(reshaped_image_elements)
    # to stack elements vertically set number_of_elements less than threshold
    if number_of_elements <= config.ELEMENT_COUNT_THRESHOLD:
        stacked_image_elements = np.vstack(reshaped_image_elements)
    else:
        # stacks to form another column of elements in the generated image
        left_elements = np.vstack(
            reshaped_image_elements[: number_of_elements // 2]
        )
        right_elements = np.vstack(
            reshaped_image_elements[number_of_elements // 2:]
        )
        pixel_diff = abs(left_elements.shape[0] - right_elements.shape[0])

        if left_elements.shape[0] < right_elements.shape[0]:
            padded_image_element = cv2.copyMakeBorder(
                left_elements,
                top=0,
                bottom=pixel_diff,
                left=0,
                right=0,
                borderType=cv2.BORDER_CONSTANT,
                value=config.CANVAS_COLOR["WHITE"],
            )
            stacked_image_elements = np.hstack(
                [padded_image_element, right_elements]
            )
        else:
            padded_image_element = cv2.copyMakeBorder(
                right_elements,
                top=0,
                bottom=pixel_diff,
                left=0,
                right=0,
                borderType=cv2.BORDER_CONSTANT,
                value=config.CANVAS_COLOR["WHITE"],
            )
            stacked_image_elements = np.hstack(
                [left_elements, padded_image_element]
            )

    return stacked_image_elements


def add_background_colour_to_generated_image(
    generated_image: Any, background_colour: str
) -> List[Sequence]:
    """
    Returns an image with desired color added to background of the image
    generated

    @ param generated_image: the image generated
    @ param background_colour: the default or selected colour
    @ return: overlayed_img
    """
    height, width, channels = generated_image.shape
    # creating a canvas with white background
    canvas = np.ones((height, width, channels), np.uint8) * 255
    canvas[:] = config.CANVAS_COLOR[background_colour]
    foreground_gray_image = cv2.cvtColor(generated_image, cv2.COLOR_RGB2GRAY)
    mask = cv2.adaptiveThreshold(
        src=foreground_gray_image,
        maxValue=255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=199,
        C=5,
    )
    mask_inv = cv2.bitwise_not(mask)
    background = cv2.bitwise_and(canvas, canvas, mask=mask)
    foreground = cv2.bitwise_and(
        generated_image, generated_image, mask=mask_inv
    )
    overlayed_img = cv2.add(foreground, background)
    return overlayed_img
