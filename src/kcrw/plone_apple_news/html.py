import re
from lxml import etree
from lxml import html
from lxml.html.clean import Cleaner
from plone import api
from plone.outputfilters.filters.resolveuid_and_caption import ResolveUIDAndCaptionFilter  # noqa: E501
from .templates import ALLOWED_HTML_TAGS
from .templates import ALLOWED_HTML_ATTRS
from .utils import get_settings


VIDEO_RE = re.compile(
    r'^https?://([^\.]+\.)?((youtube\.com)|(youtu\.be)|(vimeo\.com))'
)


def obj_url(obj):
    settings = get_settings()
    if getattr(settings, 'canonical_url', None):
        url = settings.canonical_url.rstrip('/') + obj.absolute_url(1)
    else:
        url = obj.absolute_url()
    return url


def transform_url(url):
    settings = get_settings()
    if getattr(settings, 'canonical_url', None):
        portal_url = api.portal.get().absolute_url()
        url = url.replace(portal_url.rstrip('/'),
                          settings.canonical_url.rstrip('/'))
    return url


def strip_outer(s):
    return s[5:-6]


def is_empty(el):
    if el.text and el.text.strip():
        return False
    for sub in el:
        if el.text and el.text.strip():
            return False
        if el.tail and el.tail.strip():
            return False
        return is_empty(sub)
    return True


def apple_html(text):
    html_parser = html.HTMLParser(remove_blank_text=True)
    tree = html.fragment_fromstring(
        text, create_parent=True, parser=html_parser
    )

    cleaner = Cleaner(kill_tags=['button'],
                      remove_tags=[],
                      allow_tags=ALLOWED_HTML_TAGS,
                      page_structure=True,
                      safe_attrs_only=True,
                      safe_attrs=ALLOWED_HTML_ATTRS,
                      remove_unknown_tags=False,
                      comments=True,
                      forms=True,
                      frames=True,
                      embedded=True,
                      meta=True,
                      links=True,
                      javascript=True,
                      scripts=True,
                      style=True)
    try:
        cleaner(tree)
    except AssertionError:
        # some VERY invalid HTML
        return ''
    return strip_outer(etree.tostring(tree).strip())


def el_list_to_html(els, wrapper_id=None):
    section = etree.Element('div')
    if wrapper_id is not None:
        section.set('id', wrapper_id)
    for sub_el in els:
        section.append(sub_el)
    # Filter tags and remove carriage returns
    return apple_html(etree.tostring(section)).replace('&#13;', '').strip()


def class_to_style(tree, context=None):
    """Resolve any resolveuid links"""
    for el in tree.findall('.//*[@class]'):
        classes = [c for c in el.get('class').split() if c]
        if classes:
            style = 'class-style-{}'.format('|'.join(classes))
            el.set('data-anf-textstyle', style)


def add_underlines(tree, context=None):
    """Resolve any resolveuid links"""
    for el in tree.xpath('.//*[contains(@style, "underline")]'):
        if not el.get('data-anf-textstyle'):
            el.set('data-anf-textstyle', 'style-underline')


def fix_hrefs(tree, context):
    """Resolve any resolveuid links, and fixup internal links."""
    resolver = ResolveUIDAndCaptionFilter(context)
    for el in tree.findall('.//a'):
        href = el.get('href')
        if href:
            obj, subpath, appendix = resolver.resolve_link(href)
            if obj:
                href = obj_url(obj)
                if subpath:
                    href += subpath
                if appendix:
                    href += appendix
                el.set('href', href)
            else:
                new_url = transform_url(href)
                if new_url and new_url != href:
                    el.set('href', new_url)


def find_images(el):
    imgs = el.findall('.//img')
    if el.tag != 'img' and not len(imgs):
        return []
    if el.tag == 'img':
        imgs = [el]
    return imgs


def split_images(imgs, before_anchor=None, after_anchor=None, context=None):
    """Convert img elements into data to be used in photo components"""
    resolver = ResolveUIDAndCaptionFilter(context)
    before_parts = []
    after_parts = []
    before_images = []
    after_images = []
    for img in imgs:
        insert_before = True
        src = img.get('src')
        if not src:
            continue
        image, fullimage, src, description = resolver.resolve_image(src)
        parent = img.getparent()

        # image is only moved after if it is he last element in parent
        tail = img.tail and img.tail.strip()
        if not tail and img.getnext() is None:
            insert_before = False

        # Prepend any text attached after the image to the next
        # sibling text/tail. If there's no next sibling, it will be
        # appended to the previous sibling tail. If there's no previous
        # Sibling it's appended to the parent text.
        # We move all images with tail text before the current elemet and all
        # without after. It's not ideal, but it should behave reasonably for
        # reasonable markup.
        elif tail:
            nxt = img.getnext()
            prev = img.getprevious()
            if nxt is not None and nxt.tag not in {'img', 'code', 'pre'}:
                prefix = ''
                text = (nxt.text or '').lstrip()
                if text != nxt.text:
                    prefix = ' '
                nxt.text = prefix + img.tail.rstrip() + ' ' + text
            elif prev is not None:
                tail = (prev.tail or '').rstrip()
                prev.tail = tail + ' ' + img.tail.lstrip()
            else:
                text = (parent.text or '').rstrip()
                parent.text = text + ' ' + img.tail.lstrip()
        parent.remove(img)
        data = {
            'image': image,
            'fullimage': fullimage,
            'src': src,
            'description': description,
            'classes': img.get('class', '').split(' ')
        }

        if insert_before:
            if before_anchor:
                data['anchor'] = before_anchor
            before_images.append(data)
        else:
            if after_anchor:
                data['anchor'] = after_anchor
            after_images.append(data)

    if before_images:
        before_parts = [{'type': 'body_images', 'contents': before_images}]
    if after_images:
        after_parts = [{'type': 'body_images', 'contents': after_images}]

    return before_parts, after_parts


def find_videos(el):
    matches = []
    frames = el.findall(".//iframe")
    if el.tag != 'iframe' and not len(frames):
        return matches
    if el.tag == 'iframe':
        frames = [el]
    for f in frames:
        if VIDEO_RE.match(f.get('src')):
            matches.append(f)
    return matches


def split_videos(frames, before_anchor=None, after_anchor=None, context=None):
    embeds = []
    for f in frames:
        component = {
            "role": "embedwebvideo",
            "URL": f.get('src'),
            'layout': 'bodyVideoEmbed',
            'style': 'bodyVideoEmbedStyle',
        }
        if after_anchor:
            component["anchor"] = {
                "target": after_anchor,
                "targetAnchorPosition": "top"
            }
        embeds.append(component)
        f.getparent().remove(f)
    return [], embeds


class HTMLProcessorRegistry(object):
    def __init__(self):
        self.filter_registry = []
        self.splitter_registry = []

    def register_filter(self, name, filter, before=None):
        self.unregister_filter(name)
        names = {s[0]: i for i, s in enumerate(self.filter_registry)}
        position = len(self.filter_registry)
        if before and before in names:
            position = names[before]
        elif before == '*':
            position = 0
        self.filter_registry.insert(position, (name, filter))

    def unregister_filter(self, name):
        names = {s[0]: i for i, s in enumerate(self.filter_registry)}
        if name in names:
            self.filter_registry.pop(names[name])

    def register_splitter(self, name, matcher, splitter, before=None):
        self.unregister_splitter(name)
        names = {s[0]: i for i, s in enumerate(self.splitter_registry)}
        position = len(self.splitter_registry)
        if before and before in names:
            position = names[before]
        elif before == '*':
            position = 0
        self.splitter_registry.insert(
            position, (name, matcher, splitter)
        )

    def unregister_splitter(self, name):
        names = {s[0]: i for i, s in enumerate(self.splitter_registry)}
        if name in names:
            self.splitter_registry.pop(names[name])

    def filters(self):
        for f in self.filter_registry:
            yield f[1]

    def splitters(self):
        for s in self.splitter_registry:
            yield (s[1], s[2])


processor_registry = HTMLProcessorRegistry()
processor_registry.register_filter('class_styles', class_to_style)
processor_registry.register_filter('underlines', add_underlines)
processor_registry.register_filter('resolve_hrefs', fix_hrefs)
processor_registry.register_splitter('images', find_images, split_images)
processor_registry.register_splitter('webvideo', find_videos, split_videos)


def process_html(text, context):
    parts = []
    html_parser = html.HTMLParser(remove_blank_text=True)
    tree = html.fragment_fromstring(
        text, create_parent=True, parser=html_parser
    )

    # Apply filters
    for filter in processor_registry.filters():
        filter(tree, context)

    # Split HTML into text/body sections divided by other components
    section_count = 0
    child_count = len(tree)
    cur_els = []
    for i, el in enumerate(tree):
        before_parts = []
        after_parts = []
        for matcher, splitter in processor_registry.splitters():
            found_els = matcher(el)
            if len(found_els) == 0:
                continue

            before_anchor = 'section-{}'.format(section_count + 2)
            after_anchor = None
            if child_count > (i + 1):
                after_anchor = 'section-{}'.format(section_count + 3)
            before, after = splitter(
                found_els, before_anchor=before_anchor,
                after_anchor=after_anchor, context=context
            )
            before_parts.extend(before)
            after_parts.extend(after)

        # Determine if post-split element is empty
        if is_empty(el):
            el = None

        if before_parts:
            if len(cur_els):
                section_count += 1
                parts.append(el_list_to_html(
                    cur_els, 'section-{}'.format(section_count)
                ))
                cur_els = []
            parts.extend(before_parts)

        # Put the element into a section if it hasn't been removed
        # # from the tree
        if el is not None and el.getparent() is not None:
            cur_els.append(el)

        if after_parts:
            if len(cur_els):
                section_count += 1
                parts.append(el_list_to_html(
                    cur_els, 'section-{}'.format(section_count)
                ))
                cur_els = []
            parts.extend(after_parts)

    if cur_els:
        section_count += 1
        parts.append(el_list_to_html(
            cur_els, 'section-{}'.format(section_count)
        ))

    return parts
