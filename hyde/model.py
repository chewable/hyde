# -*- coding: utf-8 -*-
"""
Contains data structures and utilities for hyde.
"""
from hyde.fs import File, Folder
import codecs
import yaml

from hyde.util import getLoggerWithNullHandler
logger = getLoggerWithNullHandler('hyde.engine')

class Expando(object):
    """
    A generic expando class that creates attributes from
    the passed in dictionary.
    """

    def __init__(self, d):
        super(Expando, self).__init__()
        self.update(d)

    def __iter__(self):
        """
        Returns an iterator for all the items in the
        dictionary as key value pairs.
        """
        return self.__dict__.iteritems()

    def update(self, d):
        """
        Updates the expando with a new dictionary
        """
        d = d or {}
        if isinstance(d, dict):
            for key, value in d.items():
                self.set_expando(key, value)
        elif isinstance(d, Expando):
            self.update(d.__dict__)

    def set_expando(self, key, value):
        """
        Sets the expando attribute after
        transforming the value.
        """
        setattr(self, key, self.transform(value))

    def transform(self, primitive):
        """
        Creates an expando object, a sequence of expando objects or just
        returns the primitive based on the primitive's type.
        """
        if isinstance(primitive, dict):
            return Expando(primitive)
        elif isinstance(primitive, (tuple, list, set, frozenset)):
            seq = type(primitive)
            return seq(self.transform(attr) for attr in primitive)
        else:
            return primitive


class Context(object):
    """
    Wraps the context related functions and utilities.
    """

    @staticmethod
    def load(sitepath, ctx):
        """
        Load context from config data and providers.
        """
        context = {}
        try:
            context.update(ctx.data.__dict__)
            for provider_name, resource_name in ctx.providers.__dict__.items():
                res = File(Folder(sitepath).child(resource_name))
                if res.exists:
                    context[provider_name] = yaml.load(res.read_all())
        except AttributeError:
            # No context data found
            pass
        return context


class Config(Expando):
    """
    Represents the hyde configuration file
    """

    def __init__(self, sitepath, config_file=None, config_dict=None):
        default_config = dict(
            content_root='content',
            deploy_root='deploy',
            media_root='media',
            layout_root='layout',
            media_url='/media',
            site_url='/',
            not_found='404.html',
            plugins = []
        )
        conf = dict(**default_config)
        self.sitepath = Folder(sitepath)
        conf.update(self.read_config(config_file))
        if config_dict:
            conf.update(config_dict)
        super(Config, self).__init__(conf)

    def read_config(self, config_file):
        """
        Reads the configuration file and updates this
        object while allowing for inherited configurations.
        """
        conf_file = self.sitepath.child(
                            config_file if
                                    config_file else 'site.yaml')
        conf = {}
        if File(conf_file).exists:
            logger.info("Reading site configuration from [%s]", conf_file)
            with codecs.open(conf_file, 'r', 'utf-8') as stream:
                conf = yaml.load(stream)
                if 'extends' in conf:
                    parent = self.read_config(conf['extends'])
                    parent.update(conf)
                    conf = parent
        return conf


    @property
    def deploy_root_path(self):
        """
        Derives the deploy root path from the site path
        """
        return self.sitepath.child_folder(self.deploy_root)

    @property
    def content_root_path(self):
        """
        Derives the content root path from the site path
        """
        return self.sitepath.child_folder(self.content_root)

    @property
    def media_root_path(self):
        """
        Derives the media root path from the site path
        """
        return self.sitepath.child_folder(self.media_root)

    @property
    def layout_root_path(self):
        """
        Derives the layout root path from the site path
        """
        return self.sitepath.child_folder(self.layout_root)
