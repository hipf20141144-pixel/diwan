#!/usr/bin/env python3
"""
يضيف إلى كل خط عربي طبقة ألوان (COLR/CPAL) لحركات التشكيل فقط، حتى يستطيع المتصفح
تلوين الحركات بلون مستقل عن الحروف (متصفح كروم وWebView أندرويد يرسمان الحركة بلون
الحرف الذي تحته إذا لُوّنت بـ CSS عادي).

الاستخدام:  python scripts/colorize_marks.py www/fonts
المتطلبات:  pip install fonttools brotli
"""
import glob
import os
import sys

from fontTools.colorLib.builder import buildCOLR, buildCPAL
from fontTools.ttLib import TTFont

# فتحتان…سكون، علامات إضافية، ألف خنجرية، علامات قرآنية صغيرة
MARK_CPS = (
    list(range(0x064B, 0x0660))
    + [0x0670]
    + list(range(0x06D6, 0x06DD))
    + list(range(0x06DF, 0x06E9))
    + list(range(0x06EA, 0x06EE))
)
DEFAULT_COLOR = (0.70, 0.15, 0.12, 1.0)  # أحمر داكن؛ يستبدله التطبيق باللون المختار


def subtables(lookup):
    for st in lookup.SubTable:
        yield getattr(st, "ExtSubTable", st)


def collect_marks(font):
    cmap = font.getBestCmap() or {}
    marks = {cmap[c] for c in MARK_CPS if c in cmap}

    gdef = font.get("GDEF")
    if gdef is not None and getattr(gdef.table, "GlyphClassDef", None):
        marks |= {g for g, c in gdef.table.GlyphClassDef.classDefs.items() if c == 3}

    # الصور البديلة والمركّبة للحركات (مثل الشدة مع الفتحة) تأتي من GSUB
    gsub = font.get("GSUB")
    if gsub is not None and gsub.table.LookupList:
        lookups = gsub.table.LookupList.Lookup
        changed = True
        while changed:
            changed = False
            for lk in lookups:
                for st in subtables(lk):
                    mapping = getattr(st, "mapping", None)
                    if mapping:
                        for a, b in mapping.items():
                            if a in marks:
                                for o in (b if isinstance(b, (list, tuple)) else [b]):
                                    if o not in marks:
                                        marks.add(o)
                                        changed = True
                    alts = getattr(st, "alternates", None)
                    if alts:
                        for a, lst in alts.items():
                            if a in marks:
                                for o in lst:
                                    if o not in marks:
                                        marks.add(o)
                                        changed = True
                    ligs = getattr(st, "ligatures", None)
                    if ligs:
                        for first, ligl in ligs.items():
                            for lg in ligl:
                                comps = [first] + list(lg.Component)
                                if all(c in marks for c in comps) and lg.LigGlyph not in marks:
                                    marks.add(lg.LigGlyph)
                                    changed = True
    return marks


def colorize(path):
    font = TTFont(path)
    if "COLR" in font or "CPAL" in font:
        return "تخطي (يحتوي ألواناً أصلاً)"
    marks = collect_marks(font)
    if not marks:
        return "تخطي (لا حركات)"
    glyph_map = font.getReverseGlyphMap()
    marks = {g for g in marks if g in glyph_map}
    layers = {g: [(g, 0)] for g in marks}
    font["COLR"] = buildCOLR(layers, version=0, glyphMap=glyph_map)
    font["CPAL"] = buildCPAL([[DEFAULT_COLOR]])
    font.save(path)
    return f"تم ({len(marks)} شكل للحركات)"


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "www/fonts"
    files = []
    for ext in ("woff2", "woff", "ttf", "otf"):
        files += glob.glob(os.path.join(folder, f"*.{ext}"))
    if not files:
        print("لا توجد خطوط في", folder)
        return 1
    done = failed = 0
    for p in sorted(files):
        # خطوط اللاتينية لا تحتاج معالجة
        if "-latin-" in os.path.basename(p):
            continue
        try:
            msg = colorize(p)
            print(f"{os.path.basename(p)}: {msg}")
            if msg.startswith("تم"):
                done += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"{os.path.basename(p)}: فشل — {e}")
    print(f"المعالَج: {done}، الفاشل: {failed}")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
