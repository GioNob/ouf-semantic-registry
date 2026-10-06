# CI-only custom package; unreleased upstream source, not an Alpine vendor release.
pkgname=zlib
pkgver=1.3.2.1_git20260917
pkgrel=0
pkgdesc="zlib upstream df84af25dc1942490e1d1c899a07619152a46148 (1.3.2.1-motley)"
url="https://github.com/madler/zlib"
arch="x86_64"
license="Zlib"
builddir="/source-zlib"
makedepends="build-base"
build() {
    cd "$builddir"
    grep -F '#define ZLIB_VERSION "1.3.2.1-motley"' zlib.h
    ./configure --prefix=/usr --shared
    make -j2
}
check() { cd "$builddir"; make check; }
package() {
    cd "$builddir"
    make DESTDIR="$pkgdir" install
    rm -rf "$pkgdir/usr/include" "$pkgdir/usr/lib/pkgconfig" "$pkgdir/usr/share"
    rm -f "$pkgdir/usr/lib/libz.a"
}
