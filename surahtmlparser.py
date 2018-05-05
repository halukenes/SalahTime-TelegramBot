from bs4 import BeautifulSoup


class HTMLParser:
    def __init__(self, filedir):
        self.file = filedir
        self.soup = BeautifulSoup(open(self.file, encoding="utf8"), 'html.parser')

    def get_text(self, index):
        spans_tag = self.soup.findAll('div', {'id': 'text'})[0].findAll('span')
        return spans_tag[index].text

    def get_meaning(self, index):
        spans_tag = self.soup.findAll('div', {'id': 'meaning'})[0].findAll('span')
        return spans_tag[index].text

    def get_all_sura_with_text(self):
        text = self.soup.findAll('div', {'id': 'text'})[0].findAll('span')
        return text

    def get_all_sura_with_meaning(self):
        text = self.soup.findAll('div', {'id': 'meaning'})[0].findAll('span')
        return text
