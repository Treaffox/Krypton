"""Grundoperationen auf UFO-Mastern: laden, Kompatibilität, Interpolation."""
import ufoLib2


def load_master(path):
    font = ufoLib2.Font.open(path)
    for layer in list(font.layers):
        if layer is not font.layers.defaultLayer:
            del font.layers[layer.name]
    return font


def compatible(ga, gb):
    if len(ga.contours) != len(gb.contours) or len(ga.components) != len(gb.components):
        return False
    for ca, cb in zip(ga.contours, gb.contours):
        if [p.type for p in ca.points] != [p.type for p in cb.points]:
            return False
    return all(ca.baseGlyph == cb.baseGlyph for ca, cb in zip(ga.components, gb.components))


def _l(a, b, t):
    return a + (b - a) * t


def lerp_glyph_into(target, ga, gb, t):
    for ct, ca, cb in zip(target.contours, ga.contours, gb.contours):
        for pt, pa, pb in zip(ct.points, ca.points, cb.points):
            pt.x, pt.y = round(_l(pa.x, pb.x, t)), round(_l(pa.y, pb.y, t))
    for kt, ka, kb in zip(target.components, ga.components, gb.components):
        vals = [_l(x, y, t) for x, y in zip(tuple(ka.transformation), tuple(kb.transformation))]
        vals[4], vals[5] = round(vals[4]), round(vals[5])
        kt.transformation = type(ka.transformation)(*vals)
    bn = {a.name: a for a in gb.anchors}
    for at, aa in zip(target.anchors, ga.anchors):
        ab = bn.get(aa.name)
        if ab is not None:
            at.x, at.y = round(_l(aa.x, ab.x, t)), round(_l(aa.y, ab.y, t))
    target.width = round(_l(ga.width, gb.width, t))


def full_intermediate(fa, fb, t, sparse, muted=()):
    """Vollständiger Zwischenmaster: fa→fb bei t, Glyphen aus dem dünnen Master
    `sparse` (außer stummgeschalteten) ersetzen die Interpolation."""
    out = load_master(fa.path)
    bad = []
    for g in out:
        if g.name not in fb or not compatible(g, fb[g.name]):
            bad.append(g.name)
            continue
        lerp_glyph_into(g, fa[g.name], fb[g.name], t)
    used = []
    for g in sparse:
        if g.name in muted or g.name not in out:
            continue
        if not compatible(out[g.name], g):
            bad.append(g.name)
            continue
        out.layers.defaultLayer.insertGlyph(g, name=g.name, overwrite=True)
        used.append(g.name)
    for attr in ("xHeight", "capHeight", "ascender", "descender"):
        setattr(out.info, attr, getattr(sparse.info, attr))
    return out, bad, used
