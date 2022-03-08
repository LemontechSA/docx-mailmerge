import unittest
import tempfile
from os import path
from lxml import etree

from mailmerge import MailMerge, NAMESPACES
from tests.utils import EtreeMixin, get_document_body_part

class FormattingTest(EtreeMixin, unittest.TestCase):

    def setUp(self):
        self.open_docx(path.join(path.dirname(__file__), 'test_one_simple_field.docx'))
        zi, part = self.get_part()
        self.replacement_parts = {zi: part}
        self.simple_merge_field = part.getroot().find('.//{%(w)s}fldSimple' % NAMESPACES)
    
    def _test_formats(self, flag, format_tests):
        for formatting, value_list in format_tests.items():
            rows = [{'fieldname': value} for value, _ in value_list]
            # print(formatting)

            instr = 'MERGEFIELD fieldname {} "{}"'.format(flag, formatting)
            self.simple_merge_field.set('{%(w)s}instr' % NAMESPACES, instr)
            with MailMerge(self.get_new_docx(self.replacement_parts)) as document:
                self.assertEqual(document.get_merge_fields(), {'fieldname'})
                document.merge_templates(rows, 'page_break')

                with tempfile.TemporaryFile() as outfile:
                    document.write(outfile)

            output_fields = get_document_body_part(document).getroot().xpath('.//w:r/w:t/text()', namespaces=NAMESPACES)
            self.assertEqual(output_fields, [output_value for _, output_value in value_list])

    
    def test_number(self):
        self._test_formats(
            '\\#',
            {
                "0.00": [
                    (25, "25.00"),
                    (0, "0.00"),
                    (345.12314, "345.12")
                    ],
                "#,#00": [
                    (25, "25"),
                    (0, "00"),
                    (32345.12314, "32,345")
                    ],
                "#,###.##": [
                    (0, "0.00"),
                    (23423, "23,423.00")
                ],
                "N3": [
                    (25, "25.000"),
                    (0, "0.000"),
                    (345.12314, "345.123")
                    ],
                "P3": [
                    (25, "2500.000%"),
                    (0, "0.000%"),
                    (345.12314, "34512.314%")
                    ],
                "##%": [
                    (0.25, "25%"),
                    (0, "0%"),
                    (0.034512314, "3%")
                    ],
            })

    def test_date(self):
        self._test_formats(
            '\\@', 
            {  
                
            }
        )

    def test_text(self):
        self._test_formats(
            '\\*',
            {
                "Caps": [
                    ("handsome law group", "Handsome Law Group"),
                    ("HANDSOME  LAW GROUP", "Handsome  Law Group")
                ],
                "FirstCap": [
                    ("handsome law group", "Handsome law group"),
                ],
                "Upper": [
                    ("Handsome Law Group", "HANDSOME LAW GROUP"),
                ],
                "Lower": [
                    ("Handsome Law Group", "handsome law group"),
                ],
                "Invalid": [
                    ("handsome Law Group", "handsome Law Group"),
                ]
            })

    def test_text_before(self):
        self._test_formats(
            '\\b',
            {
                " - ": [
                    ("handsome law group", " - handsome law group"),
                    ("", "")
                ]
            }
        )

    def test_text_afterward(self):
        self._test_formats(
            '\\f',
            {
                " - ": [
                    ("handsome law group", "handsome law group - "),
                    ("", "")
                ]
            }
        )

    def tearDown(self):
        self.docx_zipfile.close()