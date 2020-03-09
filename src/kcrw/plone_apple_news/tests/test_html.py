import unittest
try:
    from unittest import mock
except ImportError:
    import mock
from lxml import etree
from kcrw.plone_apple_news.html import HTMLProcessorRegistry
from kcrw.plone_apple_news.html import class_to_style
from kcrw.plone_apple_news.html import el_list_to_html
from kcrw.plone_apple_news.html import fix_hrefs
from kcrw.plone_apple_news.html import find_images
from kcrw.plone_apple_news.html import split_images
from kcrw.plone_apple_news.html import find_videos
from kcrw.plone_apple_news.html import split_videos
from kcrw.plone_apple_news.html import strip_outer
from kcrw.plone_apple_news.html import process_html


class TestElementListToHTML(unittest.TestCase):

    def test_strip_outer(self):
        text = '<div>something<p>something else</p></div>'
        output = strip_outer(text)
        self.assertEquals(output, 'something<p>something else</p>')

    def test_combines_and_cleans(self):
        els = [etree.Element('p'), etree.Element('iframe'),
               etree.Element('p'), etree.Element('script'),
               etree.Element('p')]
        els[0].text = 'P1 text'
        els[0].set('class', 'class1')
        els[0].set('id', 'id1')
        els[0].set('random', 'random1')
        els[1].tail = ' After iframe'
        els[2].text = 'P2 text'
        els[2].tail = ' Some tail\r\n'
        els[2].set('data-anf-textstyle', 'class-style-p2')
        output = el_list_to_html(els, 'section-1')
        self.assertEquals(
            output,
            '<div id="section-1"><p id="id1">P1 text</p> After iframe'
            '<p data-anf-textstyle="class-style-p2">P2 text</p> Some tail\n<p/></div>'
        )


class TestHTMLRegistry(unittest.TestCase):
    """Test that kcrw.plone_apple_news is properly installed."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.registry = HTMLProcessorRegistry()

    def test_register_filter(self):
        registry = self.registry
        registry.register_filter('test1', 'filter1')
        self.assertEquals(
            tuple(registry.filters()), ('filter1',)
        )

    def test_delete_filter(self):
        registry = self.registry
        registry.register_filter('test1', 'filter1')
        registry.unregister_filter('test1')
        self.assertEquals(
            tuple(registry.filters()), ()
        )

    def test_replace_filter(self):
        registry = self.registry
        registry.register_filter('test1', 'filter1')
        registry.register_filter('test1', 'filter_replaced')
        self.assertEquals(
            tuple(registry.filters()), ('filter_replaced',)
        )

    def test_register_filter_with_position(self):
        registry = self.registry
        registry.register_filter('test1', 'filter1')
        registry.register_filter('test2', 'filter2')
        registry.register_filter('test0', 'filter0', before='test1')
        registry.register_filter('test1.5', 'filter1.5', before='test2')
        registry.register_filter('test-1', 'filter-1', before='*')
        self.assertEquals(
            tuple(registry.filters()),
            ('filter-1', 'filter0', 'filter1', 'filter1.5', 'filter2')
        )

    def test_register_splitter(self):
        registry = self.registry
        registry.register_splitter('test1', 'match1', 'split1')
        self.assertEquals(
            tuple(registry.splitters()), (('match1', 'split1'),)
        )

    def test_delete_splitter(self):
        registry = self.registry
        registry.register_splitter('test1', 'match1', 'split1')
        registry.unregister_splitter('test1')
        self.assertEquals(
            tuple(registry.splitters()), ()
        )

    def test_replace_splitter(self):
        registry = self.registry
        registry.register_splitter('test1', 'match1', 'split1')
        registry.register_splitter('test1', 'match_replaced', 'split_replaced')
        self.assertEquals(
            tuple(registry.splitters()),
            (('match_replaced', 'split_replaced'),)
        )

    def test_register_splitter_with_position(self):
        registry = self.registry
        registry.register_splitter('test1', 'match1', 'split1')
        registry.register_splitter('test2', 'match2', 'split2')
        registry.register_splitter('test0', 'match0', 'split0', before='test1')
        registry.register_splitter('test1.5', 'match1.5', 'split1.5',
                                   before='test2')
        registry.register_splitter('test-1', 'match-1', 'split-1', before='*')
        self.assertEquals(
            tuple(registry.splitters()),
            (('match-1', 'split-1'), ('match0', 'split0'),
             ('match1', 'split1'), ('match1.5', 'split1.5'),
             ('match2', 'split2'))
        )


@mock.patch(
    'plone.outputfilters.filters.resolveuid_and_caption.ResolveUIDAndCaptionFilter.resolve_link',  # noqa: E501
    side_effect=lambda href: ('obj-' + href, '/updated', '?nonsense')
)
@mock.patch('kcrw.plone_apple_news.html.obj_url', side_effect=lambda obj: obj)
class TestHTMLFilters(unittest.TestCase):
    """Test that kcrw.plone_apple_news is properly installed."""

    def setUp(self):
        self.tree = etree.Element('div')

    def test_class_to_style(self, obj_url, resolver):
        self.tree.set('class', 'singleClass')
        child = etree.Element('p')
        child.set('class', ' firstClass secondClass ')
        self.tree.append(child)
        class_to_style(self.tree, None)
        self.tree.get('data-anf-textstyle', 'class-style-singleClass')
        child.get('data-anf-textstyle', 'class-style-firstClass|firstClass')

    def test_fix_hrefs(self, obj_url, resolver):
        child1 = etree.Element('a')
        child2 = etree.Element('a')
        child1.set('href', 'href-a')
        child2.set('href', 'href-b')
        self.tree.append(child1)
        self.tree.append(child2)
        fix_hrefs(self.tree, None)
        self.assertEquals(
            child1.get('href'), 'obj-href-a/updated?nonsense'
        )
        self.assertEquals(
            child2.get('href'), 'obj-href-b/updated?nonsense'
        )
        self.assertEquals(resolver.call_count, 2)
        self.assertEquals(obj_url.call_count, 2)


@mock.patch(
    'plone.outputfilters.filters.resolveuid_and_caption.ResolveUIDAndCaptionFilter.resolve_image',  # noqa: E501
    side_effect=lambda src: (None, None, 'replaced-src-' + src, 'Description')
)
class TestImageSplitter(unittest.TestCase):
    """Test that kcrw.plone_apple_news is properly installed."""

    def setUp(self):
        self.tree = etree.Element('div')
        self.p = etree.Element('p')
        self.img = etree.Element('img')
        self.img.set('src', 'solo')
        # Add parents for these elements
        self.tree.append(self.p)
        self.tree.append(self.img)

    def test_find_images(self, resolver):
        # returns all images in order
        all_imgs = find_images(self.tree)
        self.assertEquals(len(all_imgs), 1)
        self.assertIs(all_imgs[0], self.img)

        p_imgs = find_images(self.p)
        self.assertEquals(len(p_imgs), 0)

        img = find_images(self.img)
        self.assertEquals(len(img), 1)
        self.assertIs(img[0], self.img)

        self.p.append(etree.Element('img'))
        all_imgs = find_images(self.tree)
        self.assertEquals(len(all_imgs), 2)
        self.assertIs(all_imgs[0], self.p.find('img'))
        self.assertIs(all_imgs[1], self.img)

        p_imgs = find_images(self.p)
        self.assertEquals(len(p_imgs), 1)
        self.assertIs(p_imgs[0], self.p.find('img'))

    def test_split_solo(self, resolver):
        # Running split on an image at the root will remove it and setup a
        # component to be rendered after the currently processed set of
        # components
        self.assertEqual(len(self.tree.findall('.//img')), 1)
        before, after = split_images([self.img], after_anchor='next-p')
        self.assertEqual(len(self.tree.findall('.//img')), 0)
        self.assertEquals(len(before), 0)
        self.assertEquals(len(after), 1)
        self.assertEquals(len(after[0]['contents']), 1)
        img_info = after[0]['contents'][0]
        self.assertEquals(img_info.get('src'), 'replaced-src-solo')
        self.assertEquals(img_info.get('description'), 'Description')
        self.assertEquals(img_info.get('anchor'), 'next-p')

    def test_split_solo_with_tail(self, resolver):
        # If an image has a tail it ends up in the "before"
        self.img.tail = 'Some extra text'
        before, after = split_images([self.img], before_anchor='prev-p')
        self.assertEqual(len(self.tree.findall('.//img')), 0)
        self.assertEquals(len(before), 1)
        self.assertEquals(len(after), 0)
        self.assertEquals(len(before[0]['contents']), 1)
        img_info = before[0]['contents'][0]
        self.assertEquals(img_info.get('src'), 'replaced-src-solo')
        self.assertEquals(img_info.get('description'), 'Description')
        self.assertEquals(img_info.get('anchor'), 'prev-p')
        self.assertEquals(self.p.tail, ' Some extra text')

    def test_split_multiples(self, resolver):
        # Two images are replaced and placement depends on tail presence,
        # tail is moved to next sibling if not image, else previous or parent.
        self.p.text = 'P1 text'
        self.img.tail = 'Some extra text'
        img2 = etree.Element('img')
        img2.set('src', 'solo2')
        self.tree.append(img2)
        p2 = etree.Element('p')
        self.tree.append(p2)
        before, after = split_images([self.img, img2])
        self.assertEqual(len(self.tree.findall('.//img')), 0)
        self.assertEquals(len(before), 1)
        self.assertEquals(len(after), 0)
        self.assertEquals(len(before[0]['contents']), 2)
        img_info1 = before[0]['contents'][0]
        img_info2 = before[0]['contents'][1]
        self.assertEquals(img_info1.get('src'), 'replaced-src-solo')
        self.assertEquals(self.p.tail, ' Some extra text')
        self.assertEquals(img_info2.get('src'), 'replaced-src-solo2')

    def test_split_multiples_with_non_image_sibling(self, resolver):
        # Two images are replaced and placement depends on tail presence,
        # tails are moved through images onto the text of the next sibling.
        self.img.tail = 'Some extra text'
        p2 = etree.Element('p')
        p2.text = ' P2 text'
        self.tree.append(p2)
        img2 = etree.Element('img')
        img2.set('src', 'solo2')
        self.tree.append(img2)
        before, after = split_images([self.img, img2])
        self.assertEqual(len(self.tree.findall('.//img')), 0)
        self.assertEquals(len(before), 1)
        self.assertEquals(len(after), 1)
        self.assertEquals(len(before[0]['contents']), 1)
        self.assertEquals(len(after[0]['contents']), 1)
        img_info1 = before[0]['contents'][0]
        img_info2 = after[0]['contents'][0]
        self.assertEquals(img_info1.get('src'), 'replaced-src-solo')
        self.assertEquals(p2.text, ' Some extra text P2 text')
        self.assertEquals(img_info2.get('src'), 'replaced-src-solo2')

    def test_split_interior(self, resolver):
        # Two images are replaced and placement depends on tail presence,
        # tails are moved through images onto the text of the next sibling.
        self.p.text = 'P1 Text'
        img1 = etree.Element('img')
        img1.set('src', 'interior1')
        img1.tail = 'Image Tail'
        self.p.append(img1)
        img2 = etree.Element('img')
        img2.set('src', 'interior2')
        self.p.append(img2)

        before, after = split_images([img1, img2])
        # We removed the images in self.p, but not others
        self.assertEqual(len(self.tree.findall('.//img')), 1)
        self.assertEquals(len(before), 1)
        self.assertEquals(len(after), 1)
        self.assertEquals(len(before[0]['contents']), 1)
        self.assertEquals(len(after[0]['contents']), 1)
        img_info1 = before[0]['contents'][0]
        img_info2 = after[0]['contents'][0]
        self.assertEquals(img_info1.get('src'), 'replaced-src-interior1')
        self.assertEquals(self.p.text, 'P1 Text Image Tail')
        self.assertEquals(img_info2.get('src'), 'replaced-src-interior2')

    def test_split_interior_with_prev_elems(self, resolver):
        # Two images are replaced and placement depends on tail presence,
        # tails are moved through images onto the text of the next sibling.
        self.p.text = 'P1 text'
        span = etree.Element('span')
        span.text = 'In span'
        span.tail = ' Post span'
        self.p.append(span)
        img1 = etree.Element('img')
        img1.set('src', 'interior1')
        img1.tail = 'Image1 tail'
        self.p.append(img1)
        img2 = etree.Element('img')
        img2.set('src', 'interior2')
        img2.tail = 'Image2 tail'
        self.p.append(img2)

        before, after = split_images([img1, img2])
        # We removed the images in self.p, but not others
        self.assertEqual(len(self.tree.findall('.//img')), 1)
        self.assertEquals(len(before), 1)
        self.assertEquals(len(after), 0)
        self.assertEquals(len(before[0]['contents']), 2)
        img_info1 = before[0]['contents'][0]
        img_info2 = before[0]['contents'][1]
        self.assertEquals(img_info1.get('src'), 'replaced-src-interior1')
        self.assertEquals(img_info2.get('src'), 'replaced-src-interior2')
        self.assertEquals(span.tail, ' Post span Image1 tail Image2 tail')


class TestWebVideoSplitter(unittest.TestCase):
    """Test that kcrw.plone_apple_news is properly installed."""

    def setUp(self):
        self.tree = etree.Element('div')
        self.p = etree.Element('p')
        self.frame1 = etree.Element('iframe')
        self.frame1.set('src', 'https://www.youtube.com/embed/NBFypqjNlOA')
        # Add parents for these elements
        self.tree.append(self.p)
        self.tree.append(self.frame1)
        self.frame2 = etree.Element('iframe')
        self.frame2.set('src', 'https://nonsense.com/embed')
        self.p.append(self.frame2)
        self.frame3 = etree.Element('iframe')
        self.frame3.set('src', 'https://vimeo.com/embed/98274987')
        self.p.append(self.frame3)

    def test_find_videos(self):
        # returns all video frames in order
        matching_frames = find_videos(self.tree)
        self.assertEquals(len(matching_frames), 2)
        self.assertIs(matching_frames[0], self.frame3)
        self.assertIs(matching_frames[1], self.frame1)

        p_frames = find_videos(self.p)
        self.assertEquals(len(p_frames), 1)
        self.assertIs(p_frames[0], self.frame3)

        frame = find_videos(self.frame1)
        self.assertEquals(len(frame), 1)
        self.assertIs(frame[0], self.frame1)

    def test_split_videos(self):
        # Running split on an element containing a video will remove it
        # and create a video component to be rendered after the currently
        # processed set of components
        self.assertEqual(len(self.tree.findall('.//iframe')), 3)
        self.assertEqual(len(self.p.findall('.//iframe')), 2)

        before, after = split_videos([self.frame3], after_anchor='next-p')
        self.assertEqual(len(self.tree.findall('.//iframe')), 2)
        self.assertEqual(len(self.p.findall('.//iframe')), 1)

        self.assertEquals(len(before), 0)
        self.assertEquals(len(after), 1)
        self.assertEquals(after[0]['role'], 'embedwebvideo')
        self.assertEquals(after[0]['URL'], 'https://vimeo.com/embed/98274987')
        self.assertEquals(after[0]['anchor']['target'], 'next-p')


@mock.patch(
    'kcrw.plone_apple_news.html.processor_registry',
    new=HTMLProcessorRegistry()
)
class TestProcessHTML(unittest.TestCase):
    """Test that kcrw.plone_apple_news is properly installed."""

    def test_process_default(self):
        # By default it wraps sections with ids and cleans html
        html = ('<p id="p1" class="class1">text 1</p>\r\n'
                '<p>Text2</p><script>content</script>')
        output = process_html(html, None)
        self.assertEquals(
            output,
            ['<div id="section-1"><p id="p1">text 1</p>\n<p>Text2</p></div>']
        )

    def test_process_with_filters(self):
        from kcrw.plone_apple_news.html import processor_registry

        html = ('<p id="p1" class="class1"><a href="#">data</a>text 1</p>\r\n'
                '<p>Text2 <span id="span1">sub-text</span></p>'
                '<script>content</script>')

        def change_all_ids(el, context):
            # dummy filter removes anchors with no text
            els = el.findall('.//*[@id]')
            for sub in els:
                sub.set('id', 'changed-' + sub.get('id'))

        def add_a_id(el, context):
            # dummy filter removes anchors with no text
            els = el.findall('.//a[@href="#"]')
            for a in els:
                a.set('id', 'empty-a')

        processor_registry.register_filter('change_ids', change_all_ids)
        processor_registry.register_filter('empty_id', add_a_id)

        output = process_html(html, None)
        self.assertEquals(
            output,
            ['<div id="section-1"><p id="changed-p1">'
             '<a href="#" id="empty-a">data</a>text 1</p>\n'
             '<p>Text2 <span id="changed-span1">sub-text</span></p></div>']
        )
        processor_registry.unregister_filter('change_ids')
        processor_registry.unregister_filter('empty_id')

    def test_process_with_splitter(self):
        # Simple splitter that removes a 'special' element and adds
        # text parts before and after the containing section.
        from kcrw.plone_apple_news.html import processor_registry

        html = ('<p id="p1" class="class1">text 1</p>\r\n'
                '<p>Text 2 <special /><span id="span1">sub-text</span></p>'
                '<p>final</p>')

        def matcher(el):
            found = el.findall('special')
            return found

        def splitter(els, before_anchor, after_anchor, context):
            for el in els:
                el.getparent().remove(el)
            before = 'before-el1'
            after = 'after-el1'
            if before_anchor:
                before += '-anchor-' + before_anchor
            if after_anchor:
                after += '-anchor-' + after_anchor
            return [before], [after]

        processor_registry.register_splitter(
            'special_split', matcher, splitter
        )

        output = process_html(html, None)
        self.assertEquals(
            output,
            ['<div id="section-1"><p id="p1">text 1</p>\n</div>',
             'before-el1-anchor-section-2',
             '<div id="section-2"><p>Text 2 <span id="span1">'
             'sub-text</span></p></div>',
             'after-el1-anchor-section-3',
             '<div id="section-3"><p>final</p></div>']
        )
        processor_registry.unregister_splitter('special_split')

    def test_process_with_splitter_no_anchor(self):
        # Simple splitter that removes a 'special' element and adds
        # text parts before and after the containing section.
        from kcrw.plone_apple_news.html import processor_registry

        html = ('<p id="p1" class="class1">text 1</p>\r\n'
                '<p>Text 2 <special /><span id="span1">sub-text</span></p>')

        def matcher(el):
            found = el.findall('special')
            return found

        def splitter(els, before_anchor, after_anchor, context):
            for el in els:
                el.getparent().remove(el)
            before = 'before-el1'
            after = 'after-el1'
            if before_anchor:
                before += '-anchor-' + before_anchor
            if after_anchor:
                after += '-anchor-' + after_anchor
            return [before], [after]

        processor_registry.register_splitter(
            'special_split', matcher, splitter
        )

        output = process_html(html, None)
        self.assertEquals(
            output,
            ['<div id="section-1"><p id="p1">text 1</p>\n</div>',
             'before-el1-anchor-section-2',
             '<div id="section-2"><p>Text 2 <span id="span1">'
             'sub-text</span></p></div>',
             'after-el1']
        )
        processor_registry.unregister_splitter('special_split')
