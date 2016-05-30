# -*- coding: utf-8 -*-
import re

class NameGleaner(object):
    """Extracts metadata from filepaths of data files.

    A NameGleaner has a set of regular expressions called categories, each with
    a name. When NameGleaner.glean() is run, for each category, re.search is
    used to find metadata in a file name. Then a dict with a key for each
    category is returned where the values are the extracted metadata. For
    example, if you have a file '/path/to/file/temp=295K', you could make a
    NameGleaner with `ng = NameGleaner(temp='([0-9]+)K')`. Then re.search
    would find the value '295' and `ng.glean('/path/to/file/temp=295K')` 
    would return `{'temp': '295'}`. IMPORTANT: The pattern must use 
    parenthesis around the portion of the match that is to be extracted.
    This is because the value is extracted using `match.groups()[0]` where
    `match = re.search(pattern, filepath)`.

    Attributes:
        categories: A dict of the form name -> regex where the regex define
            what glean() will search for.
        translations: Rules for translating extracted metadata into some other
            form. Commonly, metadata will use an abbreviation, but in a plot
            you will want the full word. If you metadata abbreviates 'down' 
            as 'dn', then translate('category_name', 'dn', 'down') would
            automatically make glean() return 'down' instead of 'dn' in 
            the 'category_name' value of the dict it returns.
    """

    def __init__(self, **kwargs):
        self.categories = {}
        self.translations = {}
        self.regex_subs = {}
        for k, v in kwargs.items():
            self.add_category(k, v)

    def add_category(self, category, pattern):
        """Add a category that the gleaner will search for in the strings that
        are to be gleaned.  

        Usually this method is not needed as all categories can be added when
        the NameGleaner is constructed.

        Args:
            category: name of the category
            pattern: the pattern that will be searched for in the filename
        """
        self.categories[category] = pattern
        if category not in list(self.translations.keys()):
            self.translations[category] = {}
            self.regex_subs[category] = {}

    def remove_category(self, category):
        """Remove a category by name"""
        self.categories.pop(category, None)

    def translate(self, category=None, value=None, translation=None):
        """If `all` is set to true then the translation will be added
        for all existing categories (but not categories added later!).
        """
        self.translations[category][value] = translation

    def regex_sub(self, category, pattern, repl, count=0, flags=0):
        """Regular expression substitutions to be run on the gleaned
        metadata. This just wraps re.sub().
        """
        self.regex_subs[category][pattern] = (repl, count, flags)

    def glean(self, name, fill_obj=None):
        """Extract metadata fromt the filenames.

        Args:
            name: the filename to be gleaned
            fill_obj: if the pattern from a certain category is not found in 
                the filename, by default `None` will go in the returned dict.
                If a different value is passed to fill_obj, that value will
                go in the dict instead.
        
        Returns:
            dict: keys are the names of each category, values are the extracted
                values or in the case of no match, `fill_obj`.
        """
        result = {}
        for category, pat in list(self.categories.items()):
            match = re.search(pat, name)
            if match:
                gleaned = self._maybe_delistify(match.groups())
                result[category] = self._translated(category, gleaned)
                if result[category] == None:
                    result[category] = fill_obj
                    continue
            else:
                result[category] = fill_obj
        return result

    def gleanable(self, name):
        """Check if name matches at least one category.

        Args:
            name: string to be gleaned, probably a filepath.

        Returns:
            bool: whether at least one category found a match.
        """
        result = self.glean(name)
        for k, v in list(result.items()):
            if v != None:
                return True
        return False

    def _translated(self, category, gleaned):
        """Look in the translations dict for this category. If gleaned is a
        key, then replace gleaned with translations[category][gleaned].
        Then look in the regex_subs dict and perform those subs.
        """
        # Not sure that self.translations has keys for each category. If a
        # key doesn't exist just return the unchanged gleaned value.
        try:
            # The value corresponding to the gleaned key is the translation
            # that was added using translate(). If the translation isn't found
            # then we don't want to change anything, so gleaned is also the 
            # default.
            translated = self.translations[category].get(gleaned, gleaned)
        except:
            translated = gleaned
        try:
            for pat, (repl, count, flags) in self.regex_subs[category].items():
                translated = re.sub(pat, repl, translated, count, flags)
        except KeyError:
            pass
        return translated

    def _maybe_delistify(self, x):
        """For singleton lists, returns the item For empty lists returns None
        Otherwise returns list's first item 
        """
        if len(x) == 0:
            return None
        else:
            return x[0]
