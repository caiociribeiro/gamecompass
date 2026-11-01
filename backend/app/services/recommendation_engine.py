"""Motor puro do TCC1. Dados e notas entram somente do catálogo lido pela API."""

import math
import re

from .affinity import content_affinity, title_key

MIN_AFFINITY = 28
ENGINE_VERSION = 'rules_v1'
WINDOWS_ORDER = {'xp': 0, 'vista': 1, '7': 2, '8': 3, '8.1': 4, '10': 5, '11': 6}


def positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def windows_check(text, version, level='minimum'):
    target = 'mínimo' if level == 'minimum' else 'recomendado'
    def pending(detail):
        return {'label': 'Sistema operacional', 'ok': None, 'detail': detail}
    if version not in ('10', '11'):
        return pending('Informe e salve a versão do Windows na página de hardware.')
    if not text:
        return pending(f'Windows {target} não informado pela Steam.')
    restrictions = re.sub(r'\b(?:64[- ]?bits?|x64)\s+only\b', '64-bit', text, flags=re.I)
    if re.search(r'\b(?:server|phone|arm64|arm|only|somente|apenas|earlier|older|lower|not\s+supported)\b', restrictions, re.I):
        return pending(f'O requisito possui restrições específicas: {text}. Confira antes de jogar.')
    normalized = re.sub(r'[®™]', '', text)
    normalized = re.sub(r'windows(?=\d)', 'Windows ', normalized, flags=re.I)
    normalized = re.sub(r'(?<=\d)x(?:64|86)\b', '', normalized, flags=re.I)
    versions = []
    windows = bool(re.fullmatch('xp|vista', normalized.strip(), re.I))
    for part in re.split(r'\s*(?:[,;/]|\b(?:or|ou|and|e)\b)\s*', normalized, flags=re.I):
        if re.search(r'\bwindows\b', part, re.I):
            windows = True
        found = re.search(r'\bwindows\s*(xp|vista|7|8(?:\.1)?|10|11)\b', part, re.I)
        found = found or (re.match(r'^(xp|vista|7|8(?:\.1)?|10|11)\b', part, re.I) if windows else None)
        if found:
            windows = True
            versions.append(found[1].lower())
    if not versions:
        return pending(f'Windows {target} ainda não identificado: {text}.')
    minimum = min(versions, key=WINDOWS_ORDER.get)
    if WINDOWS_ORDER[version] == WINDOWS_ORDER[minimum] and re.search(r'\b(?:build|version|vers[aã]o|compila[cç][aã]o)\s*[:=]?\s*\d', text, re.I):
        return pending(f'Confira a atualização específica exigida: {text}.')
    ok = WINDOWS_ORDER[version] >= WINDOWS_ORDER[minimum]
    result = {'label': 'Sistema operacional', 'ok': ok, 'detail':
        f'Windows {version} (64 bits) atende à versão do requisito {target}. Steam: {text}.' if ok
        else f'Windows {version} informado; o requisito {target} indica Windows {minimum}.'}
    if not ok and minimum == '11':
        result['suggestion'] = {'name': 'Windows 11 (64 bits)', 'detail': 'Confira os requisitos de instalação do Windows antes de atualizar.'}
    return result


def replacement_options(parts, current, required, score_version, references=None):
    if not positive(required) or not score_version or not positive(current.get('performance_score')) or current.get('score_version') != score_version or current['performance_score'] >= required:
        return []
    def brand(part):
        return 'AMD' if re.match(r'^ATI\s', part['name'], re.I) else part['vendor']
    def name_key(value):
        return ' '.join(value.split()).lower()
    names = {name_key(v) for v in references or []}
    eligible = [p for p in parts if p['id'] != current['id'] and p.get('score_version') == score_version and positive(p.get('performance_score')) and p['performance_score'] >= required]
    def sort(part):
        return (part['performance_score'], -int(brand(part) == brand(current)), title_key(part['name']), part['id'])
    ordered = sorted([p for p in eligible if name_key(p['name']) in names], key=sort) + sorted([p for p in eligible if name_key(p['name']) not in names], key=sort)
    options, brands = [], set()
    for part in ordered:
        if brand(part) not in brands:
            options.append(part)
            brands.add(brand(part))
            if len(options) == 3:
                break
    return options


def replacement_part(parts, current, required, score_version):
    return next(iter(replacement_options(parts, current, required, score_version)), None)


def hardware_checks(game, profile, catalog, level='minimum'):
    if not profile:
        return []
    platform = game['platforms'].get(profile['os'], {})
    published = platform.get(level)
    notes_only = bool(published and published.get('requirements_kind') == 'notes_only')
    block = None if notes_only else published
    target = 'mínimo' if level == 'minimum' else 'recomendado'
    requirements = block.get('requirements', {}) if block else {}
    def part_check(label, kind, parts, identifier, required):
        part = next((p for p in parts if p['id'] == identifier), None)
        if part is None:
            return {'label': label, 'ok': None, 'detail': 'Selecione novamente uma peça do catálogo atual.'}
        if not positive(part.get('performance_score')) or not block or not block.get('score_version') or part.get('score_version') != block['score_version']:
            return {'label': label, 'ok': None, 'detail': f"{part['name']}: comparação com o requisito {target} pendente."}
        hardware = block.get('hardware', {}).get(kind) or {}
        alternatives = hardware.get('alternatives', [])
        known = [a for a in alternatives if a.get('component_type') == kind and a.get('status') == 'matched' and a.get('score_status') == 'classified' and a.get('score_version') == block['score_version'] and a.get('name') and positive(a.get('performance_score'))]
        if not positive(required):
            proof = next((a for a in known if part['performance_score'] >= a['performance_score']), None)
            query = (hardware.get('query') or '').strip()
            reference = query[:157] + '…' if len(query) > 160 else query
            missing = f'{kind}: campo ausente.' in block.get('issues', []) and not hardware
            if proof:
                detail = f"{part['name']} atende ao requisito {target} usando a alternativa {proof['name']}."
            elif known:
                detail = f"{part['name']}: as alternativas identificadas não confirmam atendimento; outras opções ainda precisam de avaliação."
            elif missing:
                detail = f"{part['name']}: a Steam não informou {'um processador' if kind == 'CPU' else 'uma placa de vídeo'} no requisito {target}."
            elif reference:
                detail = f"{part['name']}: referência da Steam ainda sem comparação ({reference})."
            else:
                detail = f"{part['name']}: comparação com o requisito {target} pendente."
            return {'label': label, 'ok': True if proof else None, 'detail': detail}
        ok = part['performance_score'] >= required
        manual = next((r for r in block.get('curation', []) if r['component_type'] == kind), None)
        references = [a['name'] for a in known]
        replacements = replacement_options(parts, part, required, block['score_version'], references) if not ok else []
        detail = f"{part['name']} {'atende ao' if ok else 'fica abaixo do'} requisito {target}."
        if manual:
            detail += f" Referência estimada: {' ou '.join(manual['reference_models'])}."
        result = {'label': label, 'ok': ok, 'detail': detail}
        if manual:
            result['estimated'] = True
        def option(candidate):
            return {'name': candidate['name'], 'partId': candidate['id'], 'detail':
                ('Modelo usado como referência manual para este requisito.' if manual else 'Modelo identificado no requisito do jogo.') if candidate['name'] in references
                else f'Alternativa do catálogo que atende à comparação de desempenho para o requisito {target}.'}
        if replacements:
            result['suggestion'] = {**option(replacements[0]), 'alternatives': [option(p) for p in replacements[1:]]}
        return result
    ram = requirements.get('ram_gb')
    ram_check = {'label': 'Memória RAM', 'ok': profile['ramGb'] >= ram if positive(ram) and positive(profile['ramGb']) else None,
        'detail': f"{profile['ramGb']} GB informados; {target} de {ram} GB." if positive(ram) else
        f'A Steam não informou a quantidade de RAM do requisito {target}.' if block and 'RAM: campo ausente.' in block.get('issues', [])
        else f'Quantidade de RAM do requisito {target} ainda não identificada.'}
    if positive(ram) and positive(profile['ramGb']) and profile['ramGb'] < ram:
        ram_check['suggestion'] = {'name': f'{ram} GB de RAM no total', 'detail': 'Capacidade total para atender ao requisito ' + target + '. Confira os módulos aceitos pelo computador.'}
    if not block and level == 'recommended':
        os_check = {'label': 'Sistema operacional', 'ok': None, 'detail': f'Requisito {target} não informado pela Steam.'}
    elif platform.get('native_support') is False:
        os_check = {'label': 'Sistema operacional', 'ok': False, 'detail': f"A Steam não informa suporte nativo a {profile['os']}."}
    elif platform.get('native_support') is not True:
        os_check = {'label': 'Sistema operacional', 'ok': None, 'detail': 'Suporte nativo não informado pela Steam.'}
    elif profile['os'] == 'Windows':
        os_check = windows_check(block.get('os_text') if block else None, profile.get('windowsVersion'), level)
    else:
        os_check = {'label': 'Sistema operacional', 'ok': None, 'detail': f"Suporte nativo a {profile['os']}. Confira a versão exigida: {(block or {}).get('os_text') or 'não informada'}. A versão ainda exige conferência."}
    checks = [part_check('Processador', 'CPU', catalog['CPU'], profile['cpuId'], requirements.get('cpu_score')),
              part_check('Placa de vídeo', 'GPU', catalog['GPU'], profile['gpuId'], requirements.get('gpu_score')), ram_check, os_check]
    if notes_only:
        checks = [c if c['ok'] is False else {**c, 'detail': 'A Steam publicou apenas observações neste nível; não informou uma especificação de hardware.'} for c in checks]
    return checks


def checks_compatibility(checks):
    return 'incompatible' if any(c['ok'] is False for c in checks) else 'needs_review' if not checks or any(c['ok'] is None for c in checks) else 'compatible'


def assess_hardware(game, profile, catalog, level):
    checks = hardware_checks(game, profile, catalog, level)
    block = game['platforms'].get(profile['os'], {}).get(level) if profile else None
    return {'available': bool(block and block.get('requirements_kind') != 'notes_only'), 'checks': checks, 'compatibility': checks_compatibility(checks)}


def anchors_of(user, games):
    by_id = {g['id']: g for g in games}
    return [by_id[identifier] for identifier in dict.fromkeys(user['anchorIds']) if identifier in by_id]


def describe_match(user, game, games, hardware):
    anchors = anchors_of(user, games)
    assessments = {level: assess_hardware(game, user.get('hardware'), hardware, level) for level in ('minimum', 'recommended')}
    minimum, recommended = assessments['minimum']['compatibility'], assessments['recommended']['compatibility']
    compatibility = 'compatible' if minimum == 'needs_review' and recommended == 'compatible' else minimum
    meets = ('recommended' if recommended == 'compatible' else 'minimum') if compatibility == 'compatible' else None
    return {'game': game, **content_affinity(user, game, anchors), 'checks': assessments['minimum']['checks'],
        'compatibility': compatibility, 'meets': meets,
        'estimated': any(c.get('estimated', False) for c in assessments[meets or 'minimum']['checks']),
        'assessments': assessments, 'compatible': compatibility == 'compatible', 'anchor': any(a['id'] == game['id'] for a in anchors)}


def hardware_profile_ready(profile, hardware):
    return bool(profile and positive(profile.get('ramGb')) and profile.get('os') in ('Windows', 'Linux', 'macOS')
        and (profile['os'] != 'Windows' or profile.get('windowsVersion') in ('10', '11'))
        and any(p['id'] == profile.get('cpuId') for p in hardware['CPU']) and any(p['id'] == profile.get('gpuId') for p in hardware['GPU']))


def profile_ready(user, games, hardware):
    return bool(user['genres'] and user['themes'] and len(anchors_of(user, games)) == 3 and hardware_profile_ready(user.get('hardware'), hardware))


def build_recommendations(user, games, hardware):
    if not profile_ready(user, games, hardware):
        return {'items': [], 'pending': [], 'excluded': []}
    ranked = [describe_match(user, g, games, hardware) for g in games]
    ranked = sorted([m for m in ranked if not m['anchor'] and m['affinity'] >= MIN_AFFINITY], key=lambda m: (-m['affinity'], title_key(m['game']['title']), m['game']['id']))
    return {group: [m for m in ranked if m['compatibility'] == status]
            for group, status in [('items', 'compatible'), ('pending', 'needs_review'), ('excluded', 'incompatible')]}
