#!/bin/bash
#
# Script to create pot/po/mo files 

basedir="/home/smo/Documents/gmediafinder/po"
cd "/home/smo/Documents/gmediafinder"

if [ "$1" = "cmo" ]; then
echo "genere le .mo"
## finalise en creeant le .mo
msgfmt --output-file=$basedir/fr/LC_MESSAGES/Gmediafinder.mo $basedir/fr/fr.po
msgfmt --output-file=$basedir/en/LC_MESSAGES/Gmediafinder.mo $basedir/en/en.po
exit 0
fi

## cree pot fichier glade et des .py
xgettext -k_ -kN_ -o $basedir/Gmediafinder.pot *.desktop.in GmediaFinder/*.py data/glade/*.glade

## create or update po files
LANGLIST="en fr"
for lang in $LANGLIST; do
if [ ! -e "$basedir"/$lang.po ]; then
	msginit --input=$basedir/Gmediafinder.pot --output=$basedir/$lang.po --locale=$lang_$(echo "$lang" | tr '[:lower:]' '[:upper:]')
else
	msginit --input=$basedir/Gmediafinder.pot --output=$basedir/$lang-update.po --locale=$lang_$(echo "$lang" | tr '[:lower:]' '[:upper:]')
	msgmerge -U $basedir/$lang.po $basedir/$lang-update.po
	## clean files
	rm $basedir/$lang-update.po
	rm $basedir/$lang.po~
fi
done
