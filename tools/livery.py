"""Paint the body colour texture (body_metal_detail.dds) for the BRG skin.
Side panels sit rotated about 11 degrees in the texture, so everything placed on them is rotated to follow the sill."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random, math
S = 2048; sc = S / 1024
BRG = (11, 61, 46); YEL = (242, 205, 30); ALU = (196, 199, 202)
TILT = 11.0            # degrees: forward direction of the side panels rises to the right in the texture (bottom strip)
FONT = '/System/Library/Fonts/Supplemental/Arial Bold.ttf'

def aluminium():
    random.seed(7)
    alu = Image.new('RGB', (S, S), ALU); px = alu.load()
    for y in range(S):
        row = random.randint(-10, 10)
        for x in range(0, S, 4):
            n = row + random.randint(-6, 6); c = (ALU[0] + n, ALU[1] + n, ALU[2] + n)
            for dx in range(4): px[x + dx, y] = c
    return alu.filter(ImageFilter.GaussianBlur(0.6))

def chrome_vent():
    """raised chrome louvre vent, 3 bright angled blades, about 0.19 x 0.09 m, bevelled frame; only thin shadow lines"""
    w, h = int(56 * sc), int(28 * sc); im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(70, 70, 72, 255))                      # shadow under the raised frame
    d.rectangle([2, 0, w - 1, h - 3], fill=(222, 225, 229, 255))                    # frame top, lit
    d.rectangle([6, 4, w - 5, h - 7], fill=(150, 153, 158, 255))                    # inner bevel
    sw = (w - 18) / 3
    for i in range(3):
        sx = 9 + i * sw
        d.rectangle([sx + 2, 7, sx + sw - 2, h - 10], fill=(196, 199, 204, 255))    # blade face, bright metal
        d.rectangle([sx + 2, 7, sx + sw - 2, 10], fill=(240, 242, 245, 255))        # top edge catching light
        d.rectangle([sx + 2, h - 13, sx + sw - 2, h - 10], fill=(60, 60, 64, 255))  # thin shadow under the blade
    return im

def crossed_flags():
    W, H = int(44 * sc), int(30 * sc); f = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(f)
    uj = Image.new('RGB', (W // 2, H // 2), (1, 33, 105)); ud = ImageDraw.Draw(uj); w, h = uj.size
    ud.line([(0, 0), (w, h)], fill='white', width=max(2, int(h * 0.22))); ud.line([(0, h), (w, 0)], fill='white', width=max(2, int(h * 0.22)))
    ud.line([(0, 0), (w, h)], fill=(200, 16, 46), width=max(1, int(h * 0.08))); ud.line([(0, h), (w, 0)], fill=(200, 16, 46), width=max(1, int(h * 0.08)))
    ud.rectangle([w / 2 - h * 0.17, 0, w / 2 + h * 0.17, h], fill='white'); ud.rectangle([0, h / 2 - h * 0.17, w, h / 2 + h * 0.17], fill='white')
    ud.rectangle([w / 2 - h * 0.1, 0, w / 2 + h * 0.1, h], fill=(200, 16, 46)); ud.rectangle([0, h / 2 - h * 0.1, w, h / 2 + h * 0.1], fill=(200, 16, 46))
    cq = Image.new('RGB', (W // 2, H // 2), 'white'); cd = ImageDraw.Draw(cq); n = 6; cw = w / n; ch = h / 4
    for i in range(n):
        for j in range(4):
            if (i + j) % 2 == 0: cd.rectangle([i * cw, j * ch, (i + 1) * cw, (j + 1) * ch], fill='black')
    ujm = Image.new('L', (W // 2, H // 2), 255).rotate(-20, expand=True); cqm = Image.new('L', (W // 2, H // 2), 255).rotate(20, expand=True)
    f.paste(uj.rotate(-20, expand=True), (0, int(H * 0.15)), ujm); f.paste(cq.rotate(20, expand=True), (W - cqm.size[0], int(H * 0.15)), cqm)
    fd.line([(W * 0.25, H), (W * 0.5, H * 0.35)], fill=(60, 60, 60), width=3); fd.line([(W * 0.75, H), (W * 0.5, H * 0.35)], fill=(60, 60, 60), width=3)
    return f

def name_badge():
    font = ImageFont.truetype(FONT, int(24 * sc))
    im = Image.new('RGBA', (int(170 * sc), int(36 * sc)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((int(4 * sc), int(18 * sc)), "G. ADONIS", font=font, fill=(240, 236, 224, 255), anchor='lm')
    return im

def place(out, im, cx, cy, angle):
    r = im.rotate(angle, expand=True, resample=Image.BICUBIC)
    out.paste(r, (int(cx * sc - r.size[0] / 2), int(cy * sc - r.size[1] / 2)), r)

def paint(mask_png, out_dds, check_png=None, base_map_png=None):
    mask = Image.open(mask_png).convert('RGBA').resize((S, S), Image.NEAREST)
    out = Image.new('RGB', (S, S), BRG)
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).polygon([(x * sc, y * sc) for x, y in [(470, 320), (760, 370), (760, 640), (470, 690)]], fill=255)
    out.paste(aluminium(), (0, 0), m)
    mp = mask.load(); op = out.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = mp[x, y]
            if a > 128 and g > r and x >= int(905 * sc): op[x, y] = YEL
    vent, flags, name = chrome_vent(), crossed_flags(), name_badge()
    # positions in 1024-px texture coordinates, from the body mesh's UV fit: vent high on the panel at the front,
    # flags under the scuttle, name low behind the flags (moved back 19 Oct 2026 so it clears them), exhaust hole where the elbow pierces the left panel
    # bottom strip (left side of the car): upright, tilted to follow the panel
    # bottom strip = right side of the car (the game reads v from the bottom); no exhaust there
    place(out, vent, 723, 670, TILT); place(out, flags, 478, 735, TILT); place(out, name, 392, 768, TILT)     # the right-side island sits further back: this keeps the G off the arch panel
    # top strip = left side, laid out rotated 180 degrees: exhaust hole where the elbow pierces the panel
    place(out, vent, 723, 1024 - 670, 180 - TILT); place(out, flags, 478, 1024 - 735, 180 - TILT); place(out, name, 335, 1024 - 772, 180 - TILT)


    out.convert('RGBA').save(out_dds, pixel_format='DXT5')
    if check_png and base_map_png:
        base = Image.open(base_map_png).convert('RGB').resize((S, S))
        Image.blend(out, base.point(lambda p: min(255, p * 2)), 0.3).crop((int(300 * sc), int(130 * sc), int(930 * sc), int(900 * sc))).resize((900, 1100)).save(check_png)

if __name__ == '__main__':
    import sys
    paint(sys.argv[1], sys.argv[2], *(sys.argv[3:5] if len(sys.argv) > 4 else ()))
