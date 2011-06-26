#!/usr/bin/python -u
# -*- coding: utf-8 -*-
# (Copyleft) 2008 - AWI : Aquitaine Webmédia Indépendant
# Translation.py
# For use gettext in python programs
####
import os, locale, gettext, sys

debug = 0

class Translation():
        """Gestion des traductions"""
        def __init__(self, _appli, _source_lang, _rep_trad):
                self.appli = 'gmediafinder'
                self.source_lang = _source_lang
                self.rep_trad = _rep_trad
                self.languages = self._traductions_disponibles()
                self.lang = self.use_lang(self.languages[0])

        # Création de la liste des traductions disponibles
        def _traductions_disponibles(self):
                global debug
                lst_lang = []
                try:
                        # Par défaut on essaye d'utiliser la langue désignée par la variable d'environement $LANG
                        if sys.platform == "win32":
                                env_lang = locale.getdefaultlocale()[0]
                        else:
                                env_lang = os.environ["LANG"]
                        if ("_" in env_lang):
                            env_lang = env_lang.split('_')[0]
                        if debug:
                                print "LANG=%s (environnement)" % (env_lang)
                        lst_lang.append(env_lang)
                        # Recherche dans l'arborescence standard des fichier de traduction ($lang/LC_MESSAGES/nom_appli.mo)
                        lst_trad = []
                        for lang in os.listdir(self.rep_trad):
                                if os.path.isdir(os.path.join(self.rep_trad,lang)) and lang != self.source_lang and lang != env_lang:
                                        if debug:
                                                print "the directorie %s/LC_MESSAGES exist" % (lang)
                                        lst_trad.append(lang)
                        for trad in gettext.find(self.appli, self.rep_trad, languages=lst_trad, all=True):
                                if trad != self.source_lang and trad != env_lang:
                                        if debug:
                                                print "Other available language, found valid .mo : %s)" % (trad)
                                        lst_lang.append(trad.split("/",2)[1:2][0])
                        # En dernier recours on utilise la langue originale du programme source (fallback)
                        if self.source_lang != env_lang:
                                lst_lang.append(self.source_lang)
                except Exception:
                        print "%s : ERROR : %s" % (sys.argv[0], err)
                finally:
                    if debug:
                        print "Available langs list : %s" % (lst_lang)
                    return lst_lang

        def use_lang(self, lang):
                global debug
                if debug:
                        print "Try to use language : %s ..." % (lang),
                self.my_lang = gettext.translation(self.appli, self.rep_trad, languages=[lang], fallback=True, codeset="UTF-8")
                # Fallback ?
                try:
                        # On teste une variable qui existe uniquement si instance=GNUTranslations
                        # (KeyError si instance=NullTranslations)
                        if not type(self.my_lang.__dict__['_catalog']) is None:
                                if debug:
                                        print " ok !"
                        else:
                                if debug:
                                        print " ok but empty traduction ?!"
                        self.lang = lang

                except KeyError:
                        if debug:
                                print " failed ! (fallback)"
                        self.lang = self.languages[len(self.languages) - 1]
                finally:
                        return self.lang

        def gettext(self, texte_utf8):
                return self.my_lang.gettext(texte_utf8.decode("UTF-8"))
