from constants import *
from .svg_mobject import SVGMobject
from .svg_mobject import VMobjectFromSVGPathstring
from utils.config_ops import digest_config
from utils.strings import split_string_list_to_isolate_substrings
from utils.tex_file_writing import tex_to_svg_file
from utils.simple_functions import update_without_overwrite
from mobject.mobject import Group
from mobject.geometry import Line
from mobject.types.vectorized_mobject import VGroup
from mobject.types.vectorized_mobject import VectorizedPoint
from animation.transform import ApplyMethod, MoveToTarget
from animation.creation import Uncreate, ShowCreation
from animation.indication import Indicate
import numpy as np

import operator as op
from functools import reduce

TEX_MOB_SCALE_FACTOR = 0.05


class TexSymbol(VMobjectFromSVGPathstring):
    """
    Purely a renaming of VMobjectFromSVGPathstring
    """
    pass


class SingleStringTexMobject(SVGMobject):
    CONFIG = {
        "template_tex_file": TEMPLATE_TEX_FILE,
        "stroke_width": 0,
        "fill_opacity": 1.0,
        "background_stroke_width": 5,
        "background_stroke_color": WHITE,
        "should_center": True,
        "height": None,
        "organize_left_to_right": False,
        "propagate_style_to_family": True,
        "alignment": "",
    }

    def __init__(self, tex_string, **kwargs):
        digest_config(self, kwargs)
        assert(isinstance(tex_string, str))
        self.tex_string = tex_string
        if "template_tex_file" in kwargs and \
                kwargs["template_tex_file"] == self.template_tex_file:
            del kwargs["template_tex_file"]
        file_name = tex_to_svg_file(
            self.get_modified_expression(tex_string),
            self.template_tex_file,
            **kwargs
        )
        SVGMobject.__init__(self, file_name=file_name, **kwargs)
        if self.height is None:
            self.scale(TEX_MOB_SCALE_FACTOR)
        if self.organize_left_to_right:
            self.organize_submobjects_left_to_right()

    def get_modified_expression(self, tex_string):
        result = self.alignment + " " + tex_string
        result = result.strip()
        result = self.modify_special_strings(result)
        return result

    def modify_special_strings(self, tex):
        tex = self.remove_stray_braces(tex)
        should_add_filler = reduce(op.or_, [
            # Fraction line needs something to be over
            tex == "\\over",
            tex == "\\overline",
            # Makesure sqrt has overbar
            tex == "\\sqrt",
            # Need to add blank subscript or superscript
            tex.endswith("_"),
            tex.endswith("^"),
        ])
        if should_add_filler:
            filler = "{\\quad}"
            tex += filler

        if tex == "\\substack":
            tex = "\\quad"

        if tex == "":
            tex = "\\quad"

        # Handle imbalanced \left and \right
        num_lefts, num_rights = [
            len([
                s for s in tex.split(substr)[1:]
                if s and s[0] in "(){}[]|.\\"
            ])
            for substr in ("\\left", "\\right")
        ]
        if num_lefts != num_rights:
            tex = tex.replace("\\left", "\\big")
            tex = tex.replace("\\right", "\\big")

        for context in ["array"]:
            begin_in = ("\\begin{%s}" % context) in tex
            end_in = ("\\end{%s}" % context) in tex
            if begin_in ^ end_in:
                # Just turn this into a blank string,
                # which means caller should leave a
                # stray \\begin{...} with other symbols
                tex = ""
        return tex

    def remove_stray_braces(self, tex):
        """
        Makes TexMobject resiliant to unmatched { at start
        """
        num_lefts, num_rights = [
            tex.count(char)
            for char in "{}"
        ]
        while num_rights > num_lefts:
            tex = "{" + tex
            num_lefts += 1
        while num_lefts > num_rights:
            tex = tex + "}"
            num_rights += 1
        return tex

    def get_tex_string(self):
        return self.tex_string

    def path_string_to_mobject(self, path_string, fill_color=None):
        # Overwrite superclass default to use
        # specialized path_string mobject
        return TexSymbol(
            path_string,
            color=fill_color,
            stroke_rgb=np.array([0, 0, 0]),
            fill_rgb=np.array([0, 0, 0]),
            fill_opacity=1,
            stroke_width=0,
            propagate_style_to_family=True,
        )

    def organize_submobjects_left_to_right(self):
        self.sort_submobjects(lambda p: p[0])
        return self

    def has_header(self):
        ret = True
        lines = self.tex_string.split('\n')
        if len(lines) == 1:
            return False
        first_line_indent = len(lines[0]) - len(lines[0].strip())
        for line in lines[1:]:
            if len(line) == 0:
                continue
            indent = len(line) - len(line.strip())
            if indent == first_line_indent:
                ret = False
                break
        return ret

    def flatten(self):
        if type(self.submobjects[0]).__name__ == "TexSymbol":
            return [self]
        elif type(self.submobjects[0]).__name__ == "SingleStringTexMobject":
            result = []
            for mob in self.submobjects:
                result.extend(mob.flatten())
            return result
        else:
            raise Exception("malformed SingleStringTexMobject")
            breakpoint(context=9)



class TexMobject(SingleStringTexMobject):
    CONFIG = {
        "arg_separator": " ",
        "substrings_to_isolate": [],
        "tex_to_color_map": {},
    }

    def __init__(self, *tex_strings, **kwargs):
        digest_config(self, kwargs)
        tex_strings = self.break_up_tex_strings(tex_strings)
        self.tex_strings = tex_strings
        SingleStringTexMobject.__init__(
            self, self.arg_separator.join(tex_strings), **kwargs
        )
        self.break_up_by_substrings(
            **update_without_overwrite(kwargs, self.CONFIG))
        self.set_color_by_tex_to_color_map(self.tex_to_color_map)

        if self.organize_left_to_right:
            self.organize_submobjects_left_to_right()

    def break_up_tex_strings(self, tex_strings):
        substrings_to_isolate = op.add(
            self.substrings_to_isolate,
            list(self.tex_to_color_map.keys())
        )
        split_list = split_string_list_to_isolate_substrings(
            tex_strings, *substrings_to_isolate
        )
        split_list = list(map(str.strip, split_list))
        split_list = [s for s in split_list if s != '']
        return split_list

    def break_up_by_substrings(self, **kwargs):
        """
        Reorganize existing submojects one layer
        deeper based on the structure of tex_strings (as a list
        of tex_strings)
        """
        new_submobjects = []
        curr_index = 0
        for tex_string in self.tex_strings:
            sub_tex_mob = SingleStringTexMobject(tex_string, **kwargs)
            num_submobs = len(sub_tex_mob.submobjects)
            new_index = curr_index + num_submobs
            if num_submobs == 0:
                # For cases like empty tex_strings, we want the corresponing
                # part of the whole TexMobject to be a VectorizedPoint
                # positioned in the right part of the TexMobject
                sub_tex_mob.submobjects = [VectorizedPoint()]
                last_submob_index = min(curr_index, len(self.submobjects) - 1)
                sub_tex_mob.move_to(self.submobjects[last_submob_index], RIGHT)
            else:
                sub_tex_mob.submobjects = self.submobjects[curr_index:new_index]
            new_submobjects.append(sub_tex_mob)
            curr_index = new_index
        self.submobjects = new_submobjects
        return self

    def get_parts_by_tex(self, tex, substring=True, case_sensitive=True):
        def test(tex1, tex2):
            if not case_sensitive:
                tex1 = tex1.lower()
                tex2 = tex2.lower()
            if substring:
                return tex1 in tex2
            else:
                return tex1 == tex2

        return VGroup(*[m for m in self.submobjects if test(tex, m.get_tex_string())])

    def get_part_by_tex(self, tex, **kwargs):
        all_parts = self.get_parts_by_tex(tex, **kwargs)
        return all_parts[0] if all_parts else None

    def set_color_by_tex(self, tex, color, **kwargs):
        parts_to_color = self.get_parts_by_tex(tex, **kwargs)
        for part in parts_to_color:
            part.set_color(color)
        return self

    def set_color_by_tex_to_color_map(self, texs_to_color_map, **kwargs):
        for texs, color in list(texs_to_color_map.items()):
            try:
                # If the given key behaves like tex_strings
                texs + ''
                self.set_color_by_tex(texs, color, **kwargs)
            except TypeError:
                # If the given key is a tuple
                for tex in texs:
                    self.set_color_by_tex(tex, color, **kwargs)
        return self

    def index_of_part(self, part):
        split_self = self.split()
        if part not in split_self:
            raise Exception("Trying to get index of part not in TexMobject")
        return split_self.index(part)

    def index_of_part_by_tex(self, tex, **kwargs):
        part = self.get_part_by_tex(tex, **kwargs)
        return self.index_of_part(part)

    def sort_submobjects_alphabetically(self):
        self.submobjects.sort(
            key=lambda m: m.get_tex_string()
        )

    def split(self):
        # Many old scenes assume that when you pass in a single string
        # to TexMobject, it indexes across the characters.
        if len(self.submobjects) == 1:
            return self.submobjects[0].split()
        else:
            return super(TexMobject, self).split()


class TextMobject(TexMobject):
    CONFIG = {
        "template_tex_file": TEMPLATE_TEXT_FILE,
        "alignment": "\\centering",
    }


class AlignatTexMobject(TexMobject):
    CONFIG = {
        "template_tex_file": TEMPLATE_ALIGNAT_FILE,
    }


class CodeMobject(TexMobject):
    CONFIG = {
        "template_tex_file": TEMPLATE_CODE_FILE,
        "indent_level": 4,
        "propagate_style_to_family": False,
        "repeat_cursor_dist": 0.15,
    }

    def __init__(self, *tex_strings, **kwargs):
        self.cursor_indices = []
        self.cursors = []
        TexMobject.__init__(self, *tex_strings, **kwargs)

    def break_up_tex_strings(self, tex_string):
        # only one string should be passed
        assert(len(tex_string) == 1)
        lines = tex_string[0].split('\n')
        while len(lines[0]) == 0 or lines[0].isspace():
            lines.pop(0)
        while len(lines[-1]) == 0 or lines[-1].isspace():
            lines.pop()
        indent = len(lines[0]) - len(lines[0].lstrip())
        lines = map(lambda l: l[indent:], lines)
        return ['\n'.join(lines)]

    def modify_special_strings(self, tex):
        return tex

    def break_up_by_substrings(self, **kwargs):
        index, mob = self.organize_by_blocks(self.tex_string)
        self.submobjects = mob.submobjects

    def organize_by_blocks(self, tex_string, level=0, index=0):
        # check for header
        header = True
        lines = tex_string.split('\n')
        min_indent = len(lines[0]) - len(lines[0].strip())
        for line in lines[1:]:
            if len(line) == 0:
                continue
            indent = len(line) - len(line.strip())
            if indent == min_indent:
                header = False
                break

        top_mob = SingleStringTexMobject(tex_string, **self.CONFIG)
        top_mob.submobjects = []
        if header:
            head_mob = SingleStringTexMobject(lines[0], **self.CONFIG)
            head_mob.submobjects = self.submobjects[index:index+len(lines[0].replace(" ", ""))]
            index += len(lines[0].replace(" ", ""))
            top_mob.submobjects.append(head_mob)
            lines = lines[1:]

        # add children
        i = 0
        while i < len(lines):
            cur_line = lines[i]
            if len(cur_line) == 0:
                i += 1
                continue
            cur_indent = len(cur_line) - len(cur_line.strip())
            if i+1 < len(lines):
                next_line = lines[i+1]
                next_indent = len(next_line) - len(next_line.strip()) 
            else:
                next_line = None
                next_indent = None
            if next_indent is None or cur_indent == next_indent or len(next_line) == 0:
                cur_mob = SingleStringTexMobject(lines[i], **self.CONFIG)
                cur_mob.submobjects = self.submobjects[index:index+len(lines[i].replace(" ", ""))]
                index += len(lines[i].replace(" ", ""))
                top_mob.submobjects.append(cur_mob)
            else:
                child_string = lines[i]
                j = 1
                while i+j < len(lines):
                    child_indent = len(lines[i+j]) - len(lines[i+j].strip())
                    if child_indent > cur_indent or len(lines[i+j]) == 0:
                        child_string += '\n' + lines[i+j]
                        j += 1
                    else:
                        break
                index, child_mob = self.organize_by_blocks(child_string, level=level+1, index=index)
                top_mob.submobjects.append(child_mob)
                i += j - 1
            i += 1
        return index, top_mob

    def get_child_idx(self, block):
        """
        Returns the index of the first child of block. This skips continued
        lines.
        """
        lines = block.tex_string.split("\n")
        first_line_indent = len(lines[0]) - len(lines[0].strip())
        child_idx = 1
        child_line_indent = len(lines[child_idx]) - len(lines[child_idx].strip())
        while child_line_indent == first_line_indent + 8:
            child_idx += 1
            child_line_indent = len(lines[child_idx]) - len(lines[child_idx].strip())
        return child_idx

    def recurse(self, block, arr, include_header=True, initialize_depth=-1):
        """
        Appends the child indices of block to arr.
        """
        if initialize_depth == 0:
            return
        child_idx = self.get_child_idx(block)
        arr.append(child_idx)
        next_block = block.submobjects[arr[-1]]
        if next_block.has_header():
            self.recurse(
                next_block,
                arr,
                initialize_depth=initialize_depth - 1,
            )

    def initialize_cursor_indices(self, include_header=False):
        """
        initialize array of indices denoting blocks with cursors
        """

        arr = []
        self.recurse(self, arr, include_header=include_header)
        self.cursor_indices = arr
        return self.cursor_indices

    def place_cursors(self, indices=None, block=None):
        """
        place cursors on the blocks denoted by indices if it was passed,
        otherwise the blocks denoted by self.cursor_indices
        """
        if indices is None and len(self.cursor_indices) == 0:
            raise Exception("no indices to use")
        elif indices is None:
            indices = self.cursor_indices
        if block is None:
            cur_block = self
        else:
            cur_block = block
        cursors = []
        for block_idx in indices:
            cur_block = cur_block.submobjects[block_idx]
            cursor = TexMobject("\\blacktriangleright")
            cursor.next_to(cur_block[0], LEFT)
            cursors.append(cursor)
        self.cursors.extend(cursors)
        return [ShowCreation(Group(*cursors))]

    def block_from_indices(self, indices, depth=-1):
        if depth == -1:
            depth = len(self.cursors)
        cur_depth = 0
        cur_block = self
        while cur_depth < depth:
            cur_block = cur_block.submobjects[indices[cur_depth]]
            cur_depth += 1
        return cur_block

    def advance_cursor(self, cursor_depth=-1, initialize_depth=-1):
        """
        Moves a cursor to the next block of equal level and initializes new
        cursors on the new block.
        """
        if cursor_depth < 0:
            cursor_depth = len(self.cursor_indices) + cursor_depth

        # find parent block of cursor to advance
        cur_block = self.block_from_indices(self.cursor_indices, cursor_depth)

        # calculate index of the block to advance to
        new_index = self.cursor_indices[cursor_depth] + 1
        if new_index > len(cur_block.submobjects) - 1:
            if cur_block.has_header():
                new_index = self.get_child_idx(cur_block)
            else:
                new_index = 0

        # remove old cursors and blocks
        anims = []
        for cursor in self.cursors[cursor_depth + 1:]:
            anims.append(Uncreate(cursor))
        self.cursors = self.cursors[:cursor_depth + 1]
        self.cursor_indices = self.cursor_indices[:cursor_depth + 1]
        self.cursor_indices[cursor_depth] = new_index

        # move cursor
        new_block = cur_block.submobjects[new_index]
        if new_block.has_header():
            anims.append(ApplyMethod(
                self.cursors[cursor_depth].next_to, new_block[0], LEFT))
        else:
            anims.append(ApplyMethod(
                self.cursors[cursor_depth].next_to, new_block[0], LEFT))

        if new_block.has_header():
            # add new blocks
            self.recurse(new_block, self.cursor_indices, initialize_depth=initialize_depth)

            # add new cursors
            anims.extend(self.place_cursors(
                indices=self.cursor_indices[cursor_depth + 1:],
                block=new_block,
            ))

        return anims

    def repeat_cursor_1(self, target_depth=-1):
        cursor = self.cursors[target_depth]
        anims = [ApplyMethod(cursor.shift, self.repeat_cursor_dist * LEFT)]

        # remove child cursors
        anims.append(Uncreate(Group(*self.cursors[target_depth + 1:])))
        self.cursors = self.cursors[:target_depth + 1]
        self.cursor_indices = self.cursor_indices[:target_depth + 1]

        return anims

    def repeat_cursor_2(self, target_depth=-1, initialize_depth=-1):
        cursor = self.cursors[target_depth]
        anims = [ApplyMethod(cursor.shift, self.repeat_cursor_dist * RIGHT)]

        # add child cursors
        block = self.block_from_indices(self.cursor_indices)
        self.recurse(block, self.cursor_indices, initialize_depth=initialize_depth)

        # place cursors at newly added indices
        anims.extend(self.place_cursors(
            indices=self.cursor_indices[target_depth + 1:],
            block=block,
        ))
        # anims.append(Indicate(block))

        return anims


class BulletedList(TextMobject):
    CONFIG = {
        "buff": MED_LARGE_BUFF,
        "dot_scale_factor": 2,
        # Have to include because of handle_multiple_args implementation
        "template_tex_file": TEMPLATE_TEXT_FILE,
        "alignment": "",
    }

    def __init__(self, *items, **kwargs):
        line_separated_items = [s + "\\\\" for s in items]
        TextMobject.__init__(self, *line_separated_items, **kwargs)
        for part in self:
            dot = TexMobject("\\cdot").scale(self.dot_scale_factor)
            dot.next_to(part[0], LEFT, SMALL_BUFF)
            part.add_to_back(dot)
        self.arrange_submobjects(
            DOWN,
            aligned_edge=LEFT,
            buff=self.buff
        )

    def fade_all_but(self, index_or_string, opacity=0.5):
        arg = index_or_string
        if isinstance(arg, str):
            part = self.get_part_by_tex(arg)
        elif isinstance(arg, int):
            part = self.submobjects[arg]
        else:
            raise Exception("Expected int or string, got {0}".format(arg))
        for other_part in self.submobjects:
            if other_part is part:
                other_part.set_fill(opacity=1)
            else:
                other_part.set_fill(opacity=opacity)


class TexMobjectFromPresetString(TexMobject):
    CONFIG = {
        # To be filled by subclasses
        "tex": None,
        "color": None,
    }

    def __init__(self, **kwargs):
        digest_config(self, kwargs)
        TexMobject.__init__(self, self.tex, **kwargs)
        self.set_color(self.color)


class Title(TextMobject):
    CONFIG = {
        "scale_factor": 1,
        "include_underline": True,
        "underline_width": FRAME_WIDTH - 2,
        # This will override underline_width
        "match_underline_width_to_text": False,
        "underline_buff": MED_SMALL_BUFF,
    }

    def __init__(self, *text_parts, **kwargs):
        TextMobject.__init__(self, *text_parts, **kwargs)
        self.scale(self.scale_factor)
        self.to_edge(UP)
        if self.include_underline:
            underline = Line(LEFT, RIGHT)
            underline.next_to(self, DOWN, buff=self.underline_buff)
            if self.match_underline_width_to_text:
                underline.match_width(self)
            else:
                underline.set_width(self.underline_width)
            self.add(underline)
            self.underline = underline
