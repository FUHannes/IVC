#!/bin/bash


#---- set some file locations (user dependent) ----
      BIN_DIR="bin"
      DAT_DIR="dat"
     TOOL_DIR="tools"
PSNR_BASE_DIR="$TOOL_DIR/psnr-images"
      PGM_DIR="org/pgm"
      PPM_DIR="org/ppm"


   
#---- set some names ----
     PSNR="./$BIN_DIR/psnrImg"
  HEVCEnc="./$BIN_DIR/encHEVC"
  HEVCDec="./$BIN_DIR/decHEVC"
 JPEG_PGM="./$DAT_DIR/JPEG_PGM.dat"
 JPEG_PPM="./$DAT_DIR/JPEG_PPM.dat"
 HEVC_PGM="./$DAT_DIR/HEVC_PGM.dat"
 HEVC_PPM="./$DAT_DIR/HEVC_PPM.dat"
PLOTS_PGM="resultsPGM.pdf"
PLOTS_PPM="resultsPPM.pdf"

 
#---- create folders ----
mkdir -p $BIN_DIR
mkdir -p $DAT_DIR
mkdir -p $TOOL_DIR


#----- compile psnr tool -----
if [ ! -f $PSNR ]
then
    #--- remove binaries (to be sure we use the latest one)
    BINS=($(find tools/psnr-images/ -name psnrImg -type f -executable))
    if (( ${#BINS[@]} > 1 ))
    then
	rm ${BINS[@]}
    fi
    #--- compile PSNR tool
    cd tools/psnr-images
    make release
    cd -
    #--- copy latest binary
    SRC_BIN=$(find tools/psnr-images/ -name psnrImg -type f -executable -printf '%T@ %p\n' | sort -n | tail -1 | cut -f2- -d " ")
    cp $SRC_BIN -T $PSNR
fi


#----- checkout and compile HEVC encoder/decoder -----
if [[ ! -f $HEVCEnc || ! -f $HEVCDec ]]
then
    #--- checkout ---
    svn co https://hevc.hhi.fraunhofer.de/svn/svn_HEVCSoftware/trunk/ $TOOL_DIR/HM-Software
    cd $TOOL_DIR/HM-Software/build/linux
    make release
    cd -
    cp $TOOL_DIR/HM-Software/bin/TAppEncoderStatic -T $HEVCEnc
    cp $TOOL_DIR/HM-Software/bin/TAppDecoderStatic -T $HEVCDec
fi


#----- PGM: JPEG encoding -----
if [ ! -f $JPEG_PGM ]
then
    DAT="$JPEG_PGM"
    REC="rec.pgm"
    BIT="bit.jpg"
    printf "# JPEG (using image magick)\n" > $DAT
    for ORG in $PGM_DIR/*.pgm
    do
	FILE="${ORG##*/}"
	NAME="${FILE%.*}"
	printf "\n\n# ${FILE}\n" >> $DAT
	printf "\"${NAME}\"\n"   >> $DAT
	for (( Q=1; Q<=100; Q++ ))
	do
	    convert $ORG -quality $Q $BIT
	    convert $BIT $REC
	    printf "%3d: %s\n" $Q "$($PSNR $ORG $REC $BIT)" >> $DAT
	    printf "\r$FILE:\tJPEG: %3d %%" $Q
	done
        printf "\n"
    done
    rm $BIT $REC
fi


#----- PPM: JPEG encoding -----
if [ ! -f $JPEG_PPM ]
then
    DAT="$JPEG_PPM"
    REC="rec.ppm"
    BIT="bit.jpg"
    printf "# JPEG (using image magick)\n" > $DAT
    for ORG in $PPM_DIR/*.ppm
    do
	FILE="${ORG##*/}"
	NAME="${FILE%.*}"
	printf "\n\n# ${FILE}\n" >> $DAT
	printf "\"${NAME}\"\n"   >> $DAT
	for (( Q=1; Q<=100; Q++ ))
	do
	    convert $ORG -quality $Q $BIT
	    convert $BIT $REC
	    printf "%3d: %s\n" $Q "$($PSNR $ORG $REC $BIT)" >> $DAT
	    printf "\r$FILE:\tJPEG: %3d %%" $Q
	done
        printf "\n"
    done
    rm $BIT $REC
fi


#----- PGM: HEVC encoding -----
if [ ! -f $HEVC_PGM ]
then
    DAT="$HEVC_PGM"
    RAW="img.y"
    TMP="out.y"
    REC="rec.pgm"
    BIT="bit.265"
    printf "# HEVC (using HM)\n" > $DAT
    for ORG in $PGM_DIR/*.pgm
    do
	W=$(head -2 $ORG | tail -1 | awk '{print $1}')
	H=$(head -2 $ORG | tail -1 | awk '{print $2}')
	FILE="${ORG##*/}"
	NAME="${FILE%.*}"
	printf "\n\n# ${FILE}\n" >> $DAT
	printf "\"${NAME}\"\n"   >> $DAT
	for (( Q=51; Q>=0; Q-- ))
	do
	    convert $ORG -depth 8 gray:$RAW
	    $HEVCEnc -c $TOOL_DIR/HM-Software/cfg/encoder_intra_main.cfg \
	             --InputChromaFormat=400 --Profile=main-RExt \
		     -fr 1 -wdt $W -hgt $H -f 1 -i $RAW -o $TMP -b $BIT -q $Q 2>/dev/null >/dev/null
	    $HEVCDec -b $BIT -o $RAW -d 8 2>/dev/null >/dev/null
	    convert -size ${W}x${H} -depth 8 gray:$RAW $REC
	    printf "%3d: %s\n" $Q "$($PSNR $ORG $REC $BIT)" >> $DAT
	    printf "\r$FILE:\tHEVC: %3.0f %%" $(echo "100.0*(52.0-$Q)/52.0" | bc)
	done
        printf "\n"
    done
    rm $BIT $RAW $TMP $REC
fi


#----- PPM: HEVC encoding -----
if [ ! -f $HEVC_PPM ]
then
    DAT="$HEVC_PPM"
    RAW="img.yuv"
    TMP="out.yuv"
    REC="rec.ppm"
    BIT="bit.265"
    printf "# HEVC (using HM)\n" > $DAT
    for ORG in $PPM_DIR/*.ppm
    do
	W=$(head -2 $ORG | tail -1 | awk '{print $1}')
	H=$(head -2 $ORG | tail -1 | awk '{print $2}')
	FILE="${ORG##*/}"
	NAME="${FILE%.*}"
	printf "\n\n# ${FILE}\n" >> $DAT
	printf "\"${NAME}\"\n"   >> $DAT
	for (( Q=51; Q>=0; Q-- ))
	do
	    convert $ORG -depth 8 -sampling-factor 4:2:0 yuv:$RAW
	    ./$HEVCEnc -c $TOOL_DIR/HM-Software/cfg/encoder_intra_main.cfg \
		       -fr 1 -wdt $W -hgt $H -f 1 -i $RAW -o $TMP -b $BIT -q $Q 2>/dev/null >/dev/null
	    ./$HEVCDec -b $BIT -o $RAW -d 8 2>/dev/null >/dev/null
	    convert -size ${W}x${H} -depth 8 -sampling-factor 4:2:0 yuv:$RAW $REC
	    printf "%3d: %s\n" $Q "$($PSNR $ORG $REC $BIT)" >> $DAT
	    printf "\r$FILE:\tHEVC: %3.0f %%" $(echo "100.0*(52.0-$Q)/52.0" | bc)
	done
        printf "\n"
    done
    rm $BIT $RAW $TMP $REC
fi



#====== PLOTS: PGM =======
if [ ! -f $PLOTS_PGM ]
then
    MaxBPP=2.0       # maximum bits per pixel
    DiagAspect=1.5   # aspect ratio of plot area
    MaxTSizeX=0.4    # maximum thumbnail size in x direction
    MaxTSizeY=0.6    # maximum thumbnail size in y direction

    NUM_IMG=$(cat $JPEG_PGM | grep '"' | wc -l)

    TMP_DIR="_temp"
    THUMB="$TMP_DIR/thumb.png"

    mkdir -p $TMP_DIR

    PDF_IMAGES=()

    for(( idx=1; idx<=$NUM_IMG; idx++ ))
    do
	TAG=$(cat $JPEG_PGM | grep '"' | head -$idx | tail -1)
	NAME=${TAG:1:${#TAG}-2}
	ORG=$PGM_DIR/$NAME.pgm
	GPL=$TMP_DIR/$NAME.gp
	PDF=$TMP_DIR/$NAME.pdf

	JPEG="'$JPEG_PGM' index '$NAME' using 2:4"
	TEST="'$HEVC_PGM' index '$NAME' using 2:4"

	echo $NAME
	OW=$(head -2 ${ORG} | tail -1 | awk '{print $1}')
	OH=$(head -2 ${ORG} | tail -1 | awk '{print $2}')

	convert $ORG -resize 300x300 $THUMB
	convert $THUMB ${THUMB/.png/.ppm}
	WIDTH=$(head -2 ${THUMB/.png/.ppm} | tail -1 | awk '{print $1}')
	HEIGHT=$(head -2 ${THUMB/.png/.ppm} | tail -1 | awk '{print $2}')

	XfitTSizeY=$(echo "$MaxTSizeX*$DiagAspect*$HEIGHT/$WIDTH" | bc -l)
	YfitTSizeX=$(echo "$MaxTSizeY/$DiagAspect/$HEIGHT*$WIDTH" | bc -l)
	isXFit=$(echo "$XfitTSizeY <= $MaxTSizeY" | bc -l)
	if(( $isXFit > 0 ))
	then
	    TSizeX=$MaxTSizeX
	    TSizeY=$XfitTSizeY
	else
	    TSizeY=$MaxTSizeY
	    TSizeX=$YfitTSizeX
	fi

	# create gnuplot file
	echo -e "#!/usr/bin/gnuplot -persist" > $GPL
	echo -e "" >> $GPL
	echo -e "tnsx=$TSizeX" >> $GPL
	echo -e "tnsy=$TSizeY" >> $GPL
	echo -e "minX=0.0" >> $GPL
	echo -e "maxX=$MaxBPP" >> $GPL
	echo -e "stats [minX:maxX] $JPEG name 'JPEG' nooutput" >> $GPL
        echo -e "stats [minX:maxX] $TEST name 'TEST' nooutput" >> $GPL
        echo -e "minY=2.0*floor(0.5*(JPEG_min_y>TEST_min_y ? JPEG_min_y : TEST_min_y))" >> $GPL
	echo -e "maxY=2.0*ceil( 0.5*(JPEG_max_y<TEST_max_y ? JPEG_max_y : TEST_max_y))" >> $GPL
	echo -e "" >> $GPL
	echo -e "set terminal pdfcairo transparent enhanced font \"Arial,10\" size 4.50in, 3.20in" >> $GPL
	echo -e "set output '$PDF'" >> $GPL
	echo -e "set key inside left top width 1.5 height 0.2 box" >> $GPL
	echo -e "set grid xtics ytics mxtics mytics back lt 1 lc rgb \"#d0d0d0\"  lw 1.0, lt 1 dashtype 3 lc rgb \"#d0d0d0\" lw 0.2" >> $GPL
	echo -e "set xtics 0.2" >> $GPL
	echo -e "set ytics 1.0" >> $GPL
	echo -e "set mxtics 2" >> $GPL
	echo -e "set mytics 2" >> $GPL
	echo -e "set title \"$NAME   ( ${OW} x ${OH} )\" offset 0,-0.8" >> $GPL
	echo -e "set xlabel \"bits per pixel\"" >> $GPL
	echo -e "set ylabel \"PSNR [dB]\"" >> $GPL
	echo -e "set xrange [minX:maxX]" >> $GPL
	echo -e "set yrange [minY:maxY]" >> $GPL
	echo -e "" >> $GPL
	echo -e "plot '$THUMB' binary filetype=png origin=(minX+(1-tnsx-0.02)*(maxX-minX),minY+0.03*(maxY-minY)) \\" >> $GPL
	echo -e "     dx=tnsx*(maxX-minX)/${WIDTH} dy=tnsy*(maxY-minY)/${HEIGHT} using 1:2:3 with rgbimage notitle,\\" >> $GPL
	echo -e "     $JPEG with linespoints pt 7 ps 0.15 lc \"blue\" title \"JPEG\",\\" >> $GPL
	echo -e "     $TEST with linespoints pt 7 ps 0.15 lc rgb \"red\" title \"HEVC\",\\" >> $GPL
	echo -e "# EOF" >> $GPL

	# create pdf
	gnuplot $GPL

	PDF_IMAGES=( "${PDF_IMAGES[@]}" "$PDF" )
    done
       
    pdfjoin -o $PLOTS_PGM --landscape "${PDF_IMAGES[@]}"

    rm -rf $TMP_DIR
fi



#====== PLOTS: PPM =======
if [ ! -f $PLOTS_PPM ]
then
    MaxBPP=2.0       # maximum bits per pixel
    DiagAspect=1.5   # aspect ratio of plot area
    MaxTSizeX=0.4    # maximum thumbnail size in x direction
    MaxTSizeY=0.6    # maximum thumbnail size in y direction

    NUM_IMG=$(cat $JPEG_PPM | grep '"' | wc -l)

    TMP_DIR="_temp"
    THUMB="$TMP_DIR/thumb.png"

    mkdir -p $TMP_DIR

    PDF_IMAGES=()

    for(( idx=1; idx<=$NUM_IMG; idx++ ))
    do
	TAG=$(cat $JPEG_PGM | grep '"' | head -$idx | tail -1)
	NAME=${TAG:1:${#TAG}-2}
	ORG=$PPM_DIR/$NAME.ppm
	GPL=$TMP_DIR/$NAME.gp
	PDF=$TMP_DIR/$NAME.pdf

	JPEG="'$JPEG_PPM' index '$NAME' using 2:4"
	TEST="'$HEVC_PPM' index '$NAME' using 2:4"

	echo $NAME
	OW=$(head -2 ${ORG} | tail -1 | awk '{print $1}')
	OH=$(head -2 ${ORG} | tail -1 | awk '{print $2}')

	convert $ORG -resize 300x300 $THUMB
	convert $THUMB ${THUMB/.png/.ppm}
	WIDTH=$(head -2 ${THUMB/.png/.ppm} | tail -1 | awk '{print $1}')
	HEIGHT=$(head -2 ${THUMB/.png/.ppm} | tail -1 | awk '{print $2}')

	XfitTSizeY=$(echo "$MaxTSizeX*$DiagAspect*$HEIGHT/$WIDTH" | bc -l)
	YfitTSizeX=$(echo "$MaxTSizeY/$DiagAspect/$HEIGHT*$WIDTH" | bc -l)
	isXFit=$(echo "$XfitTSizeY <= $MaxTSizeY" | bc -l)
	if(( $isXFit > 0 ))
	then
	    TSizeX=$MaxTSizeX
	    TSizeY=$XfitTSizeY
	else
	    TSizeY=$MaxTSizeY
	    TSizeX=$YfitTSizeX
	fi

	# create gnuplot file
	echo -e "#!/usr/bin/gnuplot -persist" > $GPL
	echo -e "" >> $GPL
	echo -e "tnsx=$TSizeX" >> $GPL
	echo -e "tnsy=$TSizeY" >> $GPL
	echo -e "minX=0.0" >> $GPL
	echo -e "maxX=$MaxBPP" >> $GPL
	echo -e "stats [minX:maxX] $JPEG name 'JPEG' nooutput" >> $GPL
        echo -e "stats [minX:maxX] $TEST name 'TEST' nooutput" >> $GPL
        echo -e "minY=2.0*floor(0.5*(JPEG_min_y>TEST_min_y ? JPEG_min_y : TEST_min_y))" >> $GPL
	echo -e "maxY=2.0*ceil( 0.5*(JPEG_max_y<TEST_max_y ? JPEG_max_y : TEST_max_y))" >> $GPL
	echo -e "" >> $GPL
	echo -e "set terminal pdfcairo transparent enhanced font \"Arial,10\" size 4.50in, 3.20in" >> $GPL
	echo -e "set output '$PDF'" >> $GPL
	echo -e "set key inside left top width 1.5 height 0.2 box" >> $GPL
	echo -e "set grid xtics ytics mxtics mytics back lt 1 lc rgb \"#d0d0d0\"  lw 1.0, lt 1 dashtype 3 lc rgb \"#d0d0d0\" lw 0.2" >> $GPL
	echo -e "set xtics 0.2" >> $GPL
	echo -e "set ytics 1.0" >> $GPL
	echo -e "set mxtics 2" >> $GPL
	echo -e "set mytics 2" >> $GPL
	echo -e "set title \"$NAME   ( ${OW} x ${OH} )\" offset 0,-0.8" >> $GPL
	echo -e "set xlabel \"bits per pixel\"" >> $GPL
	echo -e "set ylabel \"RGB-PSNR [dB]\"" >> $GPL
	echo -e "set xrange [minX:maxX]" >> $GPL
	echo -e "set yrange [minY:maxY]" >> $GPL
	echo -e "" >> $GPL
	echo -e "plot '$THUMB' binary filetype=png origin=(minX+(1-tnsx-0.02)*(maxX-minX),minY+0.03*(maxY-minY)) \\" >> $GPL
	echo -e "     dx=tnsx*(maxX-minX)/${WIDTH} dy=tnsy*(maxY-minY)/${HEIGHT} using 1:2:3 with rgbimage notitle,\\" >> $GPL
	echo -e "     $JPEG with linespoints pt 7 ps 0.15 lc \"blue\" title \"JPEG\",\\" >> $GPL
	echo -e "     $TEST with linespoints pt 7 ps 0.15 lc rgb \"red\" title \"HEVC\",\\" >> $GPL
	echo -e "# EOF" >> $GPL

	# create pdf
	gnuplot $GPL

	PDF_IMAGES=( "${PDF_IMAGES[@]}" "$PDF" )
    done
       
    pdfjoin -o $PLOTS_PPM --landscape "${PDF_IMAGES[@]}"

    rm -rf $TMP_DIR
fi






