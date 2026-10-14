"""Shared headless layout for saved-output display and synthetic engineering gate.

This module has no input readers, decoder, model, field or mechanics calls.
"""
from pathlib import Path


def setup(runtime, fonts):
    import sys
    sys.path.insert(0, runtime)
    import matplotlib
    if matplotlib.__version__ != '3.10.8':
        raise RuntimeError('Existing publication runtime changed')
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font = next((p for p in fonts if Path(p).is_file()), None)
    if font is None:
        raise RuntimeError('Declared font missing; no install or fallback')
    font_manager.fontManager.addfont(font)
    plt.rcParams.update({'font.family': font_manager.FontProperties(fname=font).get_name(),
                         'axes.unicode_minus': False, 'font.size': 10})
    return plt


def create(plt, np, language, title, times, measured, predictions, valid,
           bounds, color_limit, residual_limit, figure=None):
    from matplotlib.colors import Normalize
    from matplotlib.ticker import MaxNLocator
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    zh = language == 'zh'
    names = (('估计柔性形变与磁片', '磁片位姿（同一138轮模型）') if zh else
             ('Estimated deformation and discs', 'Disc poses from the same epoch-138 model'))
    colors = ('#1268aa', '#1268aa')
    assert len(predictions)==1
    fig = figure if figure is not None else plt.figure(figsize=(24, 18), dpi=100, facecolor='white')
    if figure is not None:
        fig.clear()
    heading = fig.text(.045, .979, title, fontsize=18, va='top')
    clock = fig.text(.045, .960, '', fontsize=12, va='top')
    panels = []
    for k in range(2):
        ax = fig.add_axes([.035 + .465*k, .565, .435, .365], projection='3d')
        ax.view_init(elev=25, azim=-58)
        for setter, j in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), range(3)):
            setter(bounds[0][j], bounds[1][j])
        ax.set_box_aspect(np.asarray(bounds[1])-bounds[0])
        ax.set(xlabel='X (mm)', ylabel='Y (mm)', zlabel='Z (mm)')
        ax.xaxis.labelpad = 12
        ax.set_title(names[k], pad=7, fontsize=14, color=colors[k])
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.zaxis.set_major_locator(MaxNLocator(4))
        ax.tick_params(labelsize=9, pad=1)
        cloud = ax.scatter([], [], [], s=5, c=[], cmap='bwr',
                           norm=Normalize(-color_limit, color_limit), depthshade=False)
        discs = Line3DCollection([], colors='#555555', linewidths=.65)
        ax.add_collection3d(discs, autolim=False)
        note = ax.text2D(.04, .03, '', transform=ax.transAxes, fontsize=10)
        panels.append((ax, cloud, discs, note))
    cax = fig.add_axes([.947, .625, .010, .255])
    fig.colorbar(panels[0][1], cax=cax, label='u_z (mm)')
    fig.text(.045, .548,
             ('全原生15通道：黑色实测，蓝色138轮模型；虚线为保存时刻' if zh else
              'All 15 native channels: measured (black), epoch-138 model (blue); dashed line: stored time'),
             fontsize=11, va='top')
    wave = fig.add_gridspec(3, 5, left=.055, right=.93, bottom=.253, top=.519,
                            hspace=.55, wspace=.30)
    cursors, wave_axes = [], []
    for component in range(3):
        for hall in range(5):
            channel = hall*3 + component
            ax = fig.add_subplot(wave[component, hall])
            trace = np.where(valid, measured[:, channel], np.nan)
            ax.plot(times, trace, color='black', lw=.75)
            for k, predicted in enumerate(predictions):
                ax.plot(times, np.where(valid, predicted[:, channel], np.nan), color=colors[k], lw=.7)
            ax.set_title('H%d%s' % (hall+1, 'XYZ'[component]), fontsize=10, pad=3)
            if hall == 0:
                ax.set_ylabel('B (µT)', fontsize=9)
            if component == 2:
                ax.set_xlabel('原生时间 (s)' if zh else 'Native time (s)', fontsize=9, labelpad=3)
            else:
                ax.tick_params(labelbottom=False)
            ax.tick_params(labelsize=8)
            ax.grid(alpha=.15)
            ax.set_xlim(float(times[0]), float(times[-1]))
            cursors.append(ax.axvline(float(times[0]), color='#303030', ls='--', lw=.7))
            wave_axes.append(ax)
    edges = np.r_[times[0]-(times[1]-times[0])/2, (times[:-1]+times[1:])/2,
                  times[-1]+(times[-1]-times[-2])/2]
    residual_axes = []
    for k in range(1):
        ax = fig.add_axes([.055, .151-.070*k, .875, .053])
        error = (predictions[k]-measured).T.copy()
        error[:, ~valid] = np.nan
        image = ax.pcolormesh(edges, np.arange(16), np.ma.masked_invalid(error),
                              cmap='bwr', norm=Normalize(-residual_limit, residual_limit), shading='flat')
        ax.set_ylim(15, 0)
        ax.set_yticks([1.5, 4.5, 7.5, 10.5, 13.5], ['H1', 'H2', 'H3', 'H4', 'H5'])
        fig.text(.055, .211-.070*k, ('138轮模型：15通道残差' if zh else 'Epoch-138 model: 15-channel residuals'),
                 fontsize=9, color=colors[k], va='bottom')
        ax.tick_params(labelsize=8, labelbottom=True)
        ax.set_xlim(float(times[0]), float(times[-1]))
        if k == 0:
            ax.set_xlabel('原生时间 (s)' if zh else 'Native time (s)', fontsize=9, labelpad=3)
        cursors.append(ax.axvline(float(times[0]), color='#303030', ls='--', lw=.7))
        residual_axes.append(ax)
    rcax = fig.add_axes([.947, .081, .010, .123])
    fig.colorbar(image, cax=rcax, label=('残差 (µT)' if zh else 'Residual (µT)'))
    footer = (('仅80个已保存几何时刻；其间保持画面仅为视觉持续，不是中间形变预测。未知槽不补齐。\n'
               '估计形变与磁片运动，非实测形变；名义几何仅作参考；XYZ等比例，位移倍率1；色标与视域统一。') if zh else
              ('Only 80 stored geometry times; holding an image between them is visual persistence, not an intermediate prediction. Unknown slots stay unknown.\n'
               'Estimated deformation / disc motion, not measured deformation; nominal geometry is a reference only; equal XYZ scale, displacement x1, shared bounds / color.'))
    fig.text(.045, .015, footer, fontsize=10, va='bottom', linespacing=1.5)
    return dict(fig=fig, heading=heading, clock=clock, panels=panels, cursors=cursors,
                wave_axes=wave_axes, residual_axes=residual_axes, language=language,
                names=names, color_limit=float(color_limit), bounds=bounds,
                kind='overview',physical_width_pt=1728)


def update(layout, np, nodes_top, surface_u, centers, rotations, known, seconds,
           slot, disc_radius, disc_thickness):
    zh = layout['language'] == 'zh'
    layout['clock'].set_text(('保存原生时刻' if zh else 'Stored native time')+
                             ' = %.6f s  |  %d / 80  |  ' % (seconds, slot+1)+
                             ('稀疏估计，非实测真值' if zh else 'Sparse estimate, not measured truth'))
    angle = np.linspace(0, 2*np.pi, 33)
    rings = []
    for z in (-disc_thickness/2, disc_thickness/2):
        rings.append(np.c_[disc_radius*np.cos(angle), disc_radius*np.sin(angle), np.full(33, z)])
    for k, (ax, cloud, discs, note) in enumerate(layout['panels']):
        if known[k]:
            positions = nodes_top+surface_u[k]
            cloud._offsets3d = tuple(positions[:, j] for j in range(3)) if k==0 else ([],[],[])
            # Explicit RGBA avoids stateful gray/colormap ambiguity without changing u.
            cloud.set_array(None)
            from matplotlib import colormaps
            cloud.set_facecolor(colormaps['bwr'](cloud.norm(surface_u[k][:, 2]))) if k==0 else cloud.set_facecolor([])
            lines = []
            for center, rotation in zip(centers[k], rotations[k]):
                low, high = [ring@rotation.T+center for ring in rings]
                lines.extend((low, high))
                lines.extend(np.stack((low[i], high[i])) for i in (0, 8, 16, 24))
            discs.set_segments(lines)
            note.set_text(('估计输出；非实测形变' if zh else 'Estimated output; not measured deformation') if k==0 else ('同一保存状态的磁片位姿' if zh else 'Disc poses from the same stored state'))
        else:
            cloud._offsets3d = tuple(nodes_top[:, j] for j in range(3))
            cloud.set_array(None)
            cloud.set_facecolor('#bdbdbd')
            discs.set_segments([])
            note.set_text('UNKNOWN：无输出，仅灰色名义几何' if zh else 'UNKNOWN: no output, gray nominal geometry only')
    for cursor in layout['cursors']:
        cursor.set_xdata([seconds, seconds])


def draw_and_capture(layout):
    """Capture every visible nonempty Text.draw extent at its actual draw position.

    Text3D/Axis3D have already projected their positions before reaching Text.draw.
    get_window_extent(renderer) observes that position and does not update any axis.
    Never call Axis._update_ticks/get_tightbbox after drawing.
    """
    from matplotlib.text import Text
    original = Text.draw
    if getattr(original, '_raq_capture', False):
        raise RuntimeError('Nested text capture is not allowed')
    records = []
    def capture(artist, renderer):
        if artist.get_visible() and artist.get_text():
            box = artist.get_window_extent(renderer)
            records.append((artist, dict(text=str(artist.get_text()),
                bounds=[float(v) for v in box.bounds])))
        return original(artist, renderer)
    capture._raq_capture = True
    Text.draw = capture
    try:
        layout['fig'].canvas.draw()
    finally:
        Text.draw = original
    layout['actual_text_draws'] = records
    return text_checks(layout)


def text_checks(layout):
    """Check captured actual draws, with no further tick/axis updates or draw."""
    import math
    fig = layout['fig']
    width, height = fig.canvas.get_width_height()
    records = layout['actual_text_draws']
    from matplotlib import font_manager
    from matplotlib.ft2font import FT2Font
    unique = {}
    for artist,rec in records:
        unique[(id(artist),rec['text'],tuple(rec['bounds']))] = (artist,rec)
    records_for_overlap = list(unique.values())
    min_font = min(a.get_fontsize() for a,_ in records)*layout['physical_width_pt']/(fig.get_figwidth()*72)
    if min_font < 7:
        raise ValueError('Actual physical text size below7pt')
    glyph_maps = {}
    if not records:
        raise RuntimeError('No actual text draw capture')
    owners = {}
    for ax in fig.axes:
        for artist in [ax.title, ax._left_title, ax._right_title]+list(ax.texts):
            owners[id(artist)] = ax
        for name in ('xaxis', 'yaxis', 'zaxis'):
            axis = getattr(ax, name, None)
            if axis is None:
                continue
            for artist in (axis.label, axis.offsetText):
                owners[id(artist)] = ax
            # Read only the existing tick lists. Do not query/reposition ticks.
            for tick in list(axis.majorTicks)+list(axis.minorTicks):
                for artist in (tick.label1, tick.label2):
                    owners[id(artist)] = ax
    boxes = {id(ax): list(map(float, ax.bbox.extents)) for ax in layout['wave_axes']}
    errors, draws = [], []
    for artist, rec in records:
        x, y, w, h = rec['bounds']
        if not all(map(math.isfinite, (x, y, w, h))):
            errors.append(dict(nonfinite_text_bounds=rec))
        elif w > 0 and h > 0:
            if x < 6 or y < 6 or x+w > width-6 or y+h > height-6:
                errors.append(rec)
            owner = owners.get(id(artist), artist.axes)
            if id(owner) in boxes:
                b = boxes[id(owner)]
                b[:] = [min(b[0], x), min(b[1], y), max(b[2], x+w), max(b[3], y+h)]
        font_path = font_manager.findfont(artist.get_fontproperties(),fallback_to_default=False)
        if font_path not in glyph_maps:
            glyph_maps[font_path] = FT2Font(font_path).get_charmap()
        missing = sorted(set(c for c in rec['text'] if not c.isspace() and ord(c) not in glyph_maps[font_path]))
        if missing:
            errors.append(dict(missing_glyphs=missing,text=rec['text']))
        draws.append(rec)
    rows, separations = layout['wave_axes'], []
    for i in range(10 if layout['kind']=='overview' else 0):
        above, below = boxes[id(rows[i])], boxes[id(rows[i+5])]
        gap = above[1]-below[3]
        separations.append(gap)
        if gap < 3:
            errors.append(dict(waveform_row_gap_pixels=gap, pair=[i, i+5]))
    # Identical repeated draw of the same label at the same position is one visual label.
    # Distinct labels and distinct positions are never discarded.
    for i,(_,a) in enumerate(records_for_overlap):
        x,y,w,h = a['bounds']
        if w<=0 or h<=0:
            continue
        for _,b in records_for_overlap[i+1:]:
            bx,by,bw,bh = b['bounds']
            if bw>0 and bh>0 and min(x+w,bx+bw)>max(x,bx) and min(y+h,by+bh)>max(y,by):
                errors.append(dict(actual_text_overlap=[a,b]))
    return dict(visible_text_checked=len(records), out_of_canvas=errors,
                minimum_publication_font_pt=min_font,physical_width_pt=layout['physical_width_pt'],
                waveform_row_gaps_pixels=separations, actual_draw_bounds=draws,
                canvas=[width, height], inspection_mutates_axis_positions=False)


def save_canvas(layout, path):
    """Save exactly the already drawn / checked pixels, without another draw."""
    from PIL import Image
    with path.open('xb') as stream:
        Image.frombuffer('RGBA', layout['fig'].canvas.get_width_height(),
                         layout['fig'].canvas.buffer_rgba(), 'raw', 'RGBA', 0, 1).save(stream, format='PNG')


