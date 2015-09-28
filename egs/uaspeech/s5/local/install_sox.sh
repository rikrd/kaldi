#!/usr/bin/env bash
#
# Install locally using yumdownloader, rpm2cpio, cpio
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#


mkdir -p $HOME/local

cd $HOME/local

dir=`mktemp -d` && cd ${dir}
yumdownloader --resolve sox

for pkg in ${dir}/*.rpm; do
    rpm2cpio ${pkg} | cpio -idv
done

rm -r ${dir}

echo "# Lines added by the install_sox.sh script of the kaldi UASPEECH egs" >> $HOME/.bashrc
echo "LD_LIBRARY_PATH=$HOME/local/usr/lib:$HOME/local/usr/lib64:$LD_LIBRARY_PATH" >> $HOME/.bashrc
echo "PATH=$HOME/local/usr/bin:$PATH" >> $HOME/.bashrc

cd -
