#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

curPath=`pwd`
rootPath=$(dirname "$curPath")
rootPath=$(dirname "$rootPath")
serverPath=$(dirname "$rootPath")
sourcePath=${serverPath}/source
sysName=`uname`
install_tmp=${rootPath}/tmp/mw_install.pl


version=8.4.x
PHP_VER=84


Install_php()
{
#------------------------ install start ------------------------------------#
yum install -y php84 php84-php-fpm
if [ "$?" == "0" ];then
	mkdir -p $serverPath/php-yum/${PHP_VER}
fi

#------------------------ install end ------------------------------------#
}

Uninstall_php()
{
	yum remove -y php84 php84-php-fpm php84-*
	rm -rf $serverPath/php-yum/${PHP_VER}
	echo "卸载php-${version}..." > $install_tmp
}

action=${1}
if [ "${1}" == 'install' ];then
	Install_php
else
	Uninstall_php
fi
