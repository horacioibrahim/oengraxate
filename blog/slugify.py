#coding: utf-8

import unittest
import re
from unicodedata import normalize

from django.utils.encoding import force_unicode
    
def slugify(s, unique_in=None):
    """
    Normaliza a string, converte para todas em minúscula, remove caracteres
    não alfanuméricos e converte espaços em hífens.

    Além disso, pode-se passar uma lista de slugs (`unique_in`), na qual
    o resultado será buscado. Se o slug resultante existir na lista, um
    sufixo numérico será adicionado para evitar duplicidade.
    """
    slug = force_unicode(s)
    slug = normalize('NFKD', slug).encode('ascii', 'ignore')
    slug = unicode(re.sub('[^\w\s-]', '', slug).strip().lower())
    slug = re.sub('[-\s]+', '-', slug)
    
    if unique_in and slug in unique_in:
        i = 1
        prefix = re.sub('-[1-9][0-9]*$', '', slug)
        slug = u'-'.join([prefix, unicode(i)])
        while slug in unique_in:
            i += 1
            slug = u'-'.join([prefix, unicode(i)])
    return slug


class SlugifyTestCase(unittest.TestCase):
    def test_slugify(self):
        self.assertEquals(
            slugify('Alguma Coisa É Massa'),
            'alguma-coisa-e-massa')

    def test_slugify_with_unique_in(self):
        slugs = ['a', 'b', 'c']
        self.assertEquals(
            slugify('A', slugs),
            'a-1')

        self.assertEquals(
            slugify('A-01', slugs),
            'a-01')

        self.assertEquals(
            slugify('A-02', slugs + ['a-02']),
            'a-02-1')


if __name__ == '__main__':
    unittest.main()

    
