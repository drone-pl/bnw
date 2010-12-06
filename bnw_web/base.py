# -*- coding: utf-8 -*-
from twisted.internet import epollreactor
#epollreactor.install()
from twisted.internet import reactor
from twisted.internet import interfaces, defer
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource, NoResource

import tornado.options
import tornado.twister
import tornado.web
#import tornado.escape
import logging,traceback
import simplejson as json
import txmongo
import os,random,time
import escape
from widgets import widgets
import PyRSS2Gen
import websocket_site
from datetime import datetime

import bnw_core.bnw_objects as objs
import bnw_core.post as post
from bnw_core.base import get_db

class TwistedHandler(tornado.web.RequestHandler):
    def writeandfinish(self,text):
        if not self._finished:
            self.write(text)
            self.finish()
    def errorfinish(self,text):
        print 'ALARM'
        if isinstance(text,Exception):
            self.write(str(text))
        else:
            self.write(str(text))
        self.finish()
    def json_fuckup(self,dct):
        if isinstance(dct,objs.MongoObject):
            return dct.doc
        if isinstance(dct,txmongo.ObjectId):
            return str(dct)
        else:
            raise TypeError(str(type(dct)))
    @tornado.web.asynchronous
    def get(self,*args,**kwargs):
        try:
            self.respond(*args,**kwargs).addCallbacks(self.writeandfinish,self.errorfinish)
        except Exception:
            self.write(traceback.format_exc())
            self.finish()

    @tornado.web.asynchronous
    def post(self,*args,**kwargs):
        try:
            self.respond_post(*args,**kwargs).addCallbacks(self.writeandfinish,self.errorfinish)
        except Exception:
            self.write(traceback.format_exc())
            self.finish()

ranq=(
    'Где блекджек, где мои шлюхи? Ничерта не работает!',
    'Здраствуйте. Я, Кирилл. Хотел бы чтобы вы сделали сервис, микроблог суть такова...',
    u'Шлюхи без блекджека, блекджек без шлюх.',
    u'Бабушка, смотри, я сделал двач!',
    u'БЕГЕМОТИКОВ МОЖНО!',
    u'ビリャチピスデツナフイ',
    u'Best viewed with LeechCraft on Microsoft Linux.',
    u'Я и мой ёбаный кот на фоне ковра.',
    u'''\u0428\u0300\u0310\u0314\u0301\u033e\u0303\u0352\u0308\u0314\u030e\u0334\u035c\u0334\u0341\u0341\u031c\u0325\u034d\u0355\u033c\u0319\u0331\u0359\u034e\u034d\u0318\u0440\u0367\u0364\u034b\u0305\u033d\u0367\u0308\u0310\u033d\u0306\u0310\u034b\u0364\u0366\u036c\u035b\u0303\u0311\u035e\u0327\u031b\u035e\u033a\u0356\u0356\u032f\u0316\u0438\u0312\u0365\u0364\u036f\u0342\u0363\u0310\u0309\u0311\u036b\u0309\u0311\u0489\u031b\u034f\u0338\u033b\u0355\u0347\u035a\u0324\u0355\u0345\u032f\u0331\u0333\u0349\u0444\u0314\u0343\u0301\u031a\u030d\u0357\u0362\u0321\u035e\u0334\u0334\u031f\u031e\u0359\u0319\u033b\u034d\u0326\u0345\u0354\u0324\u031e\u0442\u0310\u036b\u0302\u034a\u0304\u0303\u0365\u036a\u0328\u034f\u035c\u035c\u032b\u033a\u034d\u031e\u033c\u0348\u0329\u0325\u031c\u0354\u044b\u0305\u0351\u034c\u0352\u036b\u0352\u0300\u0365\u0350\u0364\u0305\u0358\u0315\u0338\u0334\u0331\u033a\u033c\u0320\u0326\u034d\u034d\u034d\u0331\u0316\u0354\u0316\u0331\u0349.\u0366\u0306\u0300\u0311\u030c\u036e\u0367\u0363\u036f\u0314\u0302\u035f\u0321\u0335\u0341\u0334\u032d\u033c\u032e\u0356\u0348\u0319\u0356\u0356\u0332\u032e\u032c\u034d\u0359\u033c\u032f\u0326\u032e\u032e\u0433\u034c\u036e\u030f\u0308\u0342\u036f\u031a\u0489\u0340\u0358\u031b\u035e\u0319\u032c\u0318\u0332\u0317\u0347\u0355\u0320\u0319\u0345\u0359\u033c\u0329\u035a\u043e\u0313\u0364\u033d\u0352\u030b\u0309\u0300\u0302\u0304\u0312\u0343\u030a\u0368\u035b\u0301\u030c\u0364\u0302\u0337\u0340\u0360\u0325\u032f\u0318\u0432\u0312\u0352\u0343\u030f\u031a\u0313\u0336\u0489\u031b\u035c\u0319\u0318\u033a\u0330\u032e\u033c\u031f\u033c\u0325\u031f\u0318\u0320\u031c\u043d\u033f\u0314\u0303\u0368\u0351\u0338\u0337\u0338\u0332\u031d\u0348\u0359\u0330\u031f\u033b\u031f\u0330\u031c\u031f\u0317\u034e\u033b\u033b\u034d\u043e\u0314\u0300\u030b\u036b\u0307\u033f\u0310\u036b\u034c\u0357\u0369\u0489\u0315\u0328\u0361\u035c\u031c\u0319\u0319\u0348\u034d\u032e\u032e\u033c\u0319\u0318\u031e''',
)

class BnwWebHandler(TwistedHandler):
    def get_defargs(self):
        return {
            'linkify': escape.linkify,
            'ranq': random.choice(ranq),
            'display_appeal': random.random(),
            'w': widgets,
            'auth_user': None,
        }
    def render(self,templatename,**kwargs):
        global ranq
        defargs=self.get_defargs()
        defargs.update(kwargs)
        return super(BnwWebHandler,self).render(templatename,**defargs)

    def writeandfinish(self,text):
        if isinstance(text,dict):
            self.render(self.templatename,**text)
        else:
            super(BnwWebHandler,self).writeandfinish(text)
