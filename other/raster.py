from xml.dom import minidom
from pathlib import Path
from shutil import copy, move
from os import path, remove
import fileinput
import glob
import sys
import re
import os


def stem(p):
    return Path(p).stem


def sort(l):
    # https://stackoverflow.com/a/2669120
    """ Sort the given iterable in the way that humans expect."""
    def convert(text): return int(text) if text.isdigit() else text

    def alphanum_key(key):
        return [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def svg_dir():
    return path.realpath(path.dirname(__file__))


def svg_subpath(subpath):
    return path.abspath(path.join(svg_dir(), subpath))


def get_new_svgs():
    svg_files = glob.glob(svg_subpath('*.svg'))
    return sort(svg_files)


def get_all_svgs():
    svg_files = glob.glob(svg_subpath('../icons/white/*.svg'))
    return sort(svg_files)


def sub_file(filename, pattern, repl):
    regex = re.compile(pattern, re.IGNORECASE)

    with fileinput.FileInput(filename, inplace=True) as f:
        for line in f:
            sys.stdout.write(regex.sub(repl, line))


def change_color(target_color):
    for svg_file in get_new_svgs():
        sub_file(svg_file, 'stroke\s*:\s*(#fff|#ffffff|white)',
                 'stroke:' + target_color)
        sub_file(svg_file, 'fill\s*:\s*(#fff|#ffffff|white)',
                 'fill:' + target_color)


def raster(theme, color):
    SIZES = ["256"]
    EXPORT_DIR = svg_subpath(f'../app/src/{theme}/res')
    ICON_DIR = svg_subpath(f'../icons/{color}')

    color_code = ("#fff" if color == 'white' else "#000")
    change_color(color_code)

    for svg_file in get_new_svgs():
        filename = path.basename(svg_file)
        name = stem(filename)
        copy(svg_file, path.join(ICON_DIR, filename))
        print(f'Working on {name} {theme.title()} Mode')

        for size in SIZES:
            cmd = f'inkscape --export-filename={svg_subpath(name)}.png --export-width={size} --export-height={size} {svg_subpath(name)}.svg'
            os.system(cmd)

        if size == "256":
            png_file = svg_subpath(f'{name}.png')
            copy(png_file, path.join(
                EXPORT_DIR, 'drawable-nodpi'))
            remove(png_file)


def _xml_create(pre, svg_pre, svg_suf, suf):
    output = pre
    for svg_file in get_all_svgs():
        name = stem(svg_file)
        output += f'{svg_pre}{name}{svg_suf}'
        # break
    return output + suf


def xml():
    # SVG_DIR = svg_subpath(f'../icons/white/')
    EXPORT_DIR = svg_subpath(f'../app/src/main/')

    iconpack = _xml_create(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n	 <string-array name="icon_pack" translatable="false">\n',
        '	    <item>',
        '</item>\n',
        '    </string-array>\n</resources>\n',
    )

    iconpack_file = svg_subpath('iconpack.xml')

    with open(iconpack_file, 'w+', encoding='utf-8') as f:
        f.write(iconpack)

    drawable = _xml_create(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n	 <version>1</version>\n	  <category title="New" />\n',
        '	  <item drawable="',
        '" />\n',
        '</resources>\n',
    )

    drawable_file = svg_subpath('drawable.xml')

    with open(drawable_file, 'w+', encoding='utf-8') as f:
        f.write(drawable)

    copy(iconpack_file, path.join(EXPORT_DIR, "res/xml"))
    copy(iconpack_file, path.join(EXPORT_DIR, "res/values"))
    remove(iconpack_file)

    copy(drawable_file, path.join(EXPORT_DIR, "res/xml"))
    copy(drawable_file, path.join(EXPORT_DIR, "assets"))
    remove(drawable_file)

    copy(svg_subpath('appfilter.xml'), path.join(EXPORT_DIR, "assets"))
    copy(svg_subpath('appfilter.xml'), path.join(EXPORT_DIR, "res/xml"))


def new_category():
    output = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n	<version>1</version>\n	<category title="New" />\n'

    for svg_file in get_new_svgs():
        name = stem(svg_file)
        output += f'	<item drawable="{name}" />\n'

    output += '</resources>\n'

    with open(svg_subpath('newdrawables.xml'), "w+") as f:
        f.write(output)


def sort_appfilter():
    appfilter = svg_subpath('appfilter.xml')

    with fileinput.FileInput(appfilter, encoding='utf-8') as f:
        output = ""

        for line in f:
            line = line.strip(" \t")
            line = re.sub(' +', ' ', line)
            line = re.sub(' ', '|', line)

            match line[0:4]:
                case '<!--':
                    output += f'\n{line.strip()}'
                case '<ite' | '<sca' | '<cal':
                    output += f' {line.strip()}'

    output = sort(output.split('\n'))
    output = '\n'.join(output)
    output = '\n'.join(
        [line for line in output.split('\n') if line.strip() != '']
    )
    output = re.sub('\n', '\n\n', output)
    output = re.sub(' ', '\n', output)
    output = re.sub('\n<', '\n    <', output)
    output = re.sub('\|', ' ', output)

    with open(appfilter, 'w+', encoding='utf-8') as f:
        f.write(f'<resources>\n\n{output}\n\n</resources>\n')


def merge_new_drawables(filename):
    with open(filename) as file:
        lines = file.readlines()
        drawables = []
        folder = []
        calendar = []
        numbers = []
        letters = []
        number = []

        # Get all in New
        newDrawables = []
        newest = re.compile(r'<category title="New" />')
        drawable = re.compile(r'drawable="([\w_]+)"')
        num = 0

        while lines:
            new = re.search(newest, lines[num])
            if new:
                break
            num += 1

        new = False
        num += 1
        while new:
            new = re.search(drawable, lines[num])
            if new:
                newDrawables.append(new.groups(0)[0])
                num += 1

        newDrawables.sort()

        # collect existing drawables
        for line in lines[num:]:
            new = re.search(drawable, lines[num])
            if new:
                if new.groups(0)[0].startswith('folder'):
                    folder.append(new.groups(0)[0])
                elif new.groups(0)[0].startswith('calendar_'):
                    calendar.append(new.groups(0)[0])
                elif new.groups(0)[0].startswith('letter_'):
                    letters.append(new.groups(0)[0])
                elif new.groups(0)[0].startswith('number_'):
                    numbers.append(new.groups(0)[0])
                elif new.groups(0)[0].startswith('_'):
                    number.append(new.groups(0)[0])
                else:
                    drawables.append(new.groups(0)[0])
            num += 1

        drawables += newDrawables

        # remove duplicates and sort
        drawables = list(set(drawables))
        drawables.sort()
        folder = list(set(folder))
        folder.sort()
        calendar = list(set(calendar))
        calendar.sort()

        # build
        output = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n<version>1</version>\n\n\t<category title="New" />\n\t'
        for newDrawable in newDrawables:
            output += '<item drawable="%s" />\n\t' % newDrawable

        output += '\n\t<category title="Folders" />\n\t'
        for entry in folder:
            output += '<item drawable="%s" />\n\t' % entry

        output += '\n\t<category title="Calendar" />\n\t'
        for entry in calendar:
            output += '<item drawable="%s" />\n\t' % entry

        output += '\n\t<category title="Letters" />\n\t'
        for entry in letters:
            output += '<item drawable="%s" />\n\t' % entry
        output += '\n\t<category title="Numbers" />\n\t'
        for entry in numbers:
            output += '<item drawable="%s" />\n\t' % entry
        output += '\n\t<category title="0-9" />\n\t'
        for entry in number:
            output += '<item drawable="%s" />\n\t' % entry

        output += '\n\t<category title="A" />\n\t'
        letter = "a"

        # iterate alphabet
        for entry in drawables:
            if not entry.startswith(letter):
                letter = chr(ord(letter) + 1)
                output += '\n\t<category title="%s" />\n\t' % letter.upper()
            output += '<item drawable="%s" />\n\t' % entry

        output += "\n</resources>"

        # write to new_'filename'.xml in working directory
        outFile = open(
            svg_subpath("new_" + filename.split("/")[-1].split("\\")[-1]), "w", encoding='utf-8')
        outFile.write(output)


def main():
    new_category()
    raster('dark', 'white')
    raster('light', 'black')

    for svg_file in get_new_svgs():
        remove(svg_file)

    sort_appfilter()
    xml()

    merge_new_drawables(svg_subpath('../app/src/main/res/xml/drawable.xml'))

    copy(svg_subpath('new_drawable.xml'), svg_subpath('drawable.xml'))
    remove(svg_subpath('new_drawable.xml'))
    copy(svg_subpath('drawable.xml'), svg_subpath('../app/src/main/res/xml'))
    copy(svg_subpath('drawable.xml'), svg_subpath('../app/src/main/assets'))
    remove(svg_subpath('drawable.xml'))


main()
