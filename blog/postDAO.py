__author__ = 'horacioibrahim'

import pymongo

from .utils import is_json

class PostDAO:
    """
    The Post Data Access Object handles interactions with the Post collections.
    Useful to run somethings to wrap MongoEngine
    """

    # constructor for the class
    def __init__(self, database):
        self.db = database
        self.posts = database.post # name of collection

    def search_text(self, terms, limit=100):
        """
        Search by term with Text Index and Return a set of data with
        limited numbers of document(JSON).

        args:
            terms -> an array list

        ** Default mongoDB LIMIT is 100 documents **

        IMPORTANT: Be sure your defined text index correctly:
        db.post.ensureIndex({
                                title: "text",
                                content: "text",
                                tags: "text"
                            },
                            {
                                weights: {
                                            title: 5,
                                            content: 6,
                                            tags:2
                                        }
                            })

        >>> test_collection = self.db.test_collection
        >>> test_collection.insert({"language": "english",\
                        "body": "I love Brazil", "hate": "politicians"})
        >>> is_json(search_text(['brazil',\
                    '"politicians corrupts"'])['results'][0])
        True

        MongoDB Docs considerations:
        - If the search string includes phrases, the search performs an AND
        with any other terms in the search string;
        e.g. search for "\"twinkle twinkle\" little star" searches for
        "twinkle twinkle" and ("little" or "star" or "twinkle").
        - text adds all negations to the query with the logical AND operator.
        - The text command ignores language-specific stop words, such as the
        and and in English.
        - The text command matches on the complete stemmed word. So if a document
        field contains the word blueberry, a search on the term blue will not match.
        However, blueberry or blueberries will match.

        NOTE: Text index was introduced in MongoDB release 2.4 because you
        need to explicitly enable the feature before creating a text index
        or using the text command.
        See: http://docs.mongodb.org/manual/tutorial/enable-text-search/

        In version 2.6 the support will default
        See: http://docs.mongodb.org/master/release-notes/2.6/
        """

        has_text_index = None
        collection_name = self.posts.name

        # check if terms is type array
        if type(terms) is not list:
            raise TypeError(u'terms must be type array')

        # check if has textIndex
        index_info = self.posts.index_information()
        for k, v in index_info.items():
            try:
                has_text_index = v['textIndexVersion']
                break
            except KeyError, e:
                has_text_index = False

        if has_text_index is False:
            raise TypeError(u'%s collection hasn\'t textIndex configured'
                            % collection_name)

        # prepare terms as string. This is possible +word and -word shortcuts
        normalized_terms = " ".join(terms)

        res = self.db.command('text', collection_name,
                              search=normalized_terms,
                              filter={'published':True})

        return res
