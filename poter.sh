#!/bin/bash
#
# Script to create pot/po/mo files 

basedir="$(pwd)/po"
cd "$(pwd)"

LANGLIST="en fr it ro pl_PL sr es cs_CZ de_DE ru zh_CN ar"

if [ "$1" = "cmo" ]; then
	for lang in $LANGLIST; do
		echo "genere le .mo $lang"
		## finalise en creeant le .mo
		mkdir -p $basedir/$lang/LC_MESSAGES &>/dev/null
		msgfmt --output-file=$basedir/$lang/LC_MESSAGES/gmediafinder.mo $basedir/$lang.po
	done
	exit 0
fi

## cree pot fichier glade et des .py
xgettext -k_ -kN_ -o $basedir/gmediafinder.pot $(find /home/smo/Documents/gmediafinder | egrep "\.glade|[a-zA-Z].py$|\.pot" | xargs)

## create or update po files
for lang in $LANGLIST; do
if [ ! -e "$basedir"/$lang.po ]; then
	msginit --input=$basedir/gmediafinder.pot --output=$basedir/$lang.po --locale=$lang_$(echo "$lang" | tr '[:lower:]' '[:upper:]')
else
	msginit --input=$basedir/gmediafinder.pot --output=$basedir/$lang-update.po --locale=$lang_$(echo "$lang" | tr '[:lower:]' '[:upper:]')
	msgmerge -U $basedir/$lang.po $basedir/$lang-update.po
	## clean files
	rm $basedir/$lang-update.po
	rm $basedir/$lang.po~
fi
done
