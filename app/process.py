from numpy import arange
from collections import Counter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox,LTChar, LTFigure
import sys
import pdfcrowd
import requests


def Process(link):
	if link[-4:] == ".pdf":
		response = requests.get(link)
		with open('static/temp.pdf', 'wb') as f:
    			f.write(response.content)
	elif link[-5:] == ".html":
		try:
    			client = pdfcrowd.HtmlToPdfClient('danisimm', 'e20813a7da8bdbe7b9002712f53b1ed7')
    			client.convertUrlToFile(link, 'static/temp.pdf')
		except pdfcrowd.Error as why:
    			sys.stderr.write('Pdfcrowd Error: {}\n'.format(why))
    			raise
		#path_wkhtmltopdf = r'static/wkhtmltopdf.exe'
		#config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
		#pdfkit.from_url(link, 'static/temp.pdf', configuration=config)
	else:
		des, dia = [],[]
		return des, dia
	link = "static/temp.pdf"
	script = Read_Script(link)
	c_in, s_in, c, s, = Get_Data(script)
	des, dia = Get_Script(script, c_in, s_in, c, s)
	return des, dia

class PdfMinerWrapper(object):
    def __init__(self, pdf_doc, pdf_pwd=""):
        self.pdf_doc = pdf_doc
        self.pdf_pwd = pdf_pwd

    def __enter__(self):
        #open the pdf file
        self.fp = open(self.pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(self.fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument(parser, password=self.pdf_pwd)
        # connect the parser and document objects
        parser.set_document(doc)
        self.doc=doc
        return self
    
    def _parse_pages(self):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(char_margin=3.5, all_texts = True)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
    
        for page in PDFPage.create_pages(self.doc):
            interpreter.process_page(page)
            # receive the LTPage object for this page
            layout = device.get_result()
            # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
            yield layout
    def __iter__(self): 
        return iter(self._parse_pages())
    
    def __exit__(self, _type, value, traceback):
        self.fp.close()

def Read_Script(filename):
    script = list()
    with PdfMinerWrapper(filename) as doc:
        for page in doc:    
            for tbox in page:
                if not isinstance(tbox, LTTextBox):
                    continue
                for obj in tbox:
                    script.append(obj)
    return script

def Get_Data(script):
    indents= list() 
    for obj in script:
        first = 0
        if not obj.get_text().isupper():
            for c in obj:
                if not isinstance(c, LTChar):
                    continue
                if c.get_text()==" ":
                    continue
                obj.x0 = c.x0
                first += 1
                if first == 1:
                    break  
            continue
        for c in obj:
            if not isinstance(c, LTChar):
                continue
            if c.get_text()==" ":
                continue
            obj.x0 = c.x0
            indents.append(obj.x0)
            first += 1
            if first == 1:
                break                           
    indents_counter = Counter(indents)

    if (len(indents_counter)>1):
        if indents_counter.most_common(2)[0][0] > indents_counter.most_common(2)[1][0]:
            char_indent = indents_counter.most_common(2)[0][0]
            scene_indent = indents_counter.most_common(2)[1][0]
        if indents_counter.most_common(2)[1][0] > indents_counter.most_common(2)[0][0]:
            char_indent = indents_counter.most_common(2)[1][0]
            scene_indent = indents_counter.most_common(2)[0][0]
    else:
        char_indent = indents_counter[0]
        scene_indent = indents_counter[0]

    chars_list = list()
    for obj in script:
        if not obj.get_text().isupper():
            continue
        if char_indent-5 < obj.x0 < char_indent+5:
                chars_list.append(obj.get_text().strip())
    chars_counter = Counter(chars_list)
    chars = dict(chars_counter.most_common())

    scene_list = list() 
    for obj in script:
        if not obj.get_text().isupper():
            continue
        if scene_indent-5 < obj.x0 < scene_indent+5:
                scene_list.append(obj.get_text().strip())
    scene_counter = Counter(scene_list)
    scenes = dict(scene_counter.most_common())
            
    return char_indent, scene_indent, chars, scenes

def Get_Script(script, char_indent, scene_indent, chars, scenes):
    full_description = str()
    full_dialogue = str()
    dialogue = str()
    description = str()
    c_type = ""
    for line in script:
        if line.x0 < scene_indent-10:
            continue
        if (line.get_text().isupper() and line.x0 in arange(scene_indent-5, scene_indent+5)):
            if(c_type=="dialogue"):
                full_dialogue += " " + dialogue
                dialogue = ""
                c_type = ""
            if(c_type=="description"):
                full_description += " " + description
                description = ""
                c_type = ""
        elif (line.get_text().strip() in chars.keys()):
            if(c_type=="dialogue"):
                full_dialogue += " " + dialogue
                dialogue = ""
                c_type = ""
            if(c_type=="description"):
                full_description += " " + description
                description = ""
                c_type = ""
            c_type = "dialogue"
        elif (c_type=="description"):
            description += " " + line.get_text().strip() + " "
        elif (line.x0 in arange(scene_indent-5, scene_indent+5)):
            if(c_type=="dialogue"):
                full_dialogue += " " + dialogue
                dialogue = ""
                c_type = ""
            description += " " + line.get_text().strip() + " "
            c_type = "description"
        elif (c_type == "dialogue"):
            dialogue += " " + line.get_text().strip() + " "
        else:
            continue
    return full_description, full_dialogue