"""Read-only companion byte/metadata verification; no scientific imports or calls."""
from pathlib import Path
import ast
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_SUFFIXES = {'.pt', '.pth', '.npz', '.npy', '.pkl', '.safetensors', '.h5', '.hdf5', '.onnx', '.ttf', '.otf', '.exe', '.dll'}
TEXT_SUFFIXES = {'.md', '.json', '.py', '.txt'}


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def main(metadata_only=False):
    started = time.perf_counter()
    cpu_start = time.process_time()
    manifest = read_json('MANIFEST.json')
    if manifest['model_epoch'] != 138:
        raise ValueError('Selected model mismatch')
    accepted = manifest['files']
    if len({r['path'] for r in accepted}) != len(accepted):
        raise ValueError('Duplicate manifest path')
    for row in accepted:
        target = (ROOT / row['path']).resolve()
        if not target.is_relative_to(ROOT):
            raise ValueError('Manifest path escapes repository')
        if metadata_only:
            if target.stat().st_size != row['bytes']:
                raise ValueError('Reused accepted asset stat changed: ' + row['path'])
        else:
            payload = target.read_bytes()
            if len(payload) != row['bytes'] or hashlib.sha256(payload).hexdigest() != row['sha256']:
                raise ValueError('Closed byte pin mismatch: ' + row['path'])

    files = sorted(p for p in ROOT.rglob('*') if p.is_file())
    inventory = []
    checked_links = 0
    source_syntax = 0
    private_paths = re.compile(r'(?:[A-Za-z]:[\\/](?:Users|大学)|/home/[A-Za-z]|192[.]168[.]1[.]154)')
    private_material = re.compile(r'(?:BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY|password\s*[:=]\s*[\"\x27][^\"\x27]+|' + 'ssh' + 'pass' + r'|\.aws[\\/])', re.I)
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name in {'.env', 'id_rsa', 'id_ed25519'}:
            raise ValueError('Forbidden payload: ' + relative)
        if metadata_only and path.suffix.lower() not in TEXT_SUFFIXES and path.name != '.gitignore':
            prior, = [r for r in accepted if r['path'] == relative]
            inventory.append({'path': relative, 'bytes': path.stat().st_size,
                              'sha256': prior['sha256'], 'hash_reused': True})
            continue
        payload = path.read_bytes()
        inventory.append({'path': relative, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(), 'hash_reused': False})
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == '.gitignore':
            text = payload.decode('utf-8')
            if private_paths.search(text) or private_material.search(text):
                raise ValueError('Private path/auth material in public text: ' + relative)
            if path.suffix == '.py':
                ast.parse(text, filename=relative)
                source_syntax += 1
            if path.suffix == '.md':
                for match in re.finditer(r'!?\[[^\]]*\]\(([^)]+)\)', text):
                    link = match.group(1).strip('<>')
                    if re.match(r'https?://', link) or link.startswith('#'):
                        continue
                    target = (path.parent / link.split('#', 1)[0]).resolve()
                    if not target.is_relative_to(ROOT) or not target.exists():
                        raise ValueError('Unresolved or escaping link: ' + relative + ' -> ' + link)
                    checked_links += 1

    summary = read_json('data/results_summary.json')
    curve = read_json('data/training_curve.json')
    epochs = curve['epochs']
    if len(epochs) != 161 or [r['epoch'] for r in epochs] != list(range(161)):
        raise ValueError('Curve epoch coverage mismatch')
    if epochs[0]['TRAIN_total'] is not None or any(epochs[e]['DEV_RMSE_uT'] is not None for e in range(37)):
        raise ValueError('Missing early measurements must remain null')
    if not all(epochs[e]['protocol'] == 'MODEL_REFERENCE_PRETRAIN_NOT_MEASURED_B' for e in range(1, 38)):
        raise ValueError('Early training objective distinction lost')
    for epoch, key in [(138, 'selected'), (160, 'terminal')]:
        if epochs[epoch]['DEV_RMSE_uT'] != summary[key]['RMSE_uT'] or epochs[epoch]['DEV_MAE_uT'] != summary[key]['MAE_uT']:
            raise ValueError('Curve/aggregate metric mismatch')
    if (summary['native_rows'], summary['valid_rows'], summary['raw15_scalar_count'], summary['guard_failures']) != (234195, 233791, 3506865, 0):
        raise ValueError('Evaluation denominator mismatch')
    zh = read_json('data/paper_tables_zh.json')['tables']
    en = read_json('data/paper_tables_en.json')['tables']
    numeric = lambda tables: re.findall(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?', json.dumps(tables, ensure_ascii=False))
    if len(zh) != 3 or len(en) != 3 or numeric(zh) != numeric(en):
        raise ValueError('Bilingual main table numbers differ')
    custody = read_json('source/physics_source_custody.json')
    if len(custody['files']) != 2 or any(not r['included'] for r in custody['files']):
        raise ValueError('The two authorized physics sources must be included')
    if len(list((ROOT / 'media/native').glob('*.mp4'))) != 18 or len(list((ROOT / 'media').glob('*.gif'))) != 2:
        raise ValueError('Saved media count mismatch')
    return {
        'status': 'METADATA_CLOSURE_ACCEPTED_PRIOR_ASSET_SHA_REUSED_TWO_PHYSICS_SOURCES_INCLUDED' if metadata_only else 'STATIC_COMPANION_ACCEPTED',
        'metadata_only': metadata_only, 'prior_closed_asset_hash_checks_repeated': 0 if metadata_only else len(accepted),
        'files': len(files), 'total_bytes': sum(x['bytes'] for x in inventory),
        'closed_assets': len(accepted), 'resolved_local_links': checked_links,
        'Python_syntax_only': source_syntax, 'epoch_scalar_rows': len(epochs),
        'new_training_NN_field_geometry_plot_codec_PDF_render': 0,
        'Word_visual_acceptance': False, 'fresh_training_reproduction': False,
        'all_rights_closed': False, 'publication_state_checked': False,
        'pending': ['Further open licensing and scientific reproduction remain separate.'],
        'CPU_s': time.process_time() - cpu_start, 'wall_s': time.perf_counter() - started,
        'inventory': inventory,
    }


if __name__ == '__main__':
    try:
        print(json.dumps(main(metadata_only='--metadata-only' in sys.argv[1:]), ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps({'status': 'FAIL_STOP_NO_RETRY', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise
