import os

def resolve_download_path(info_dict, ydl_instance, template_path=None):
    """Return the best-guess absolute path for the file produced by yt-dlp."""
    candidates = []

    for entry in info_dict.get('requested_downloads') or []:
        for key in ('filepath', '_filename', 'filename'):
            path = entry.get(key)
            if path:
                candidates.append(path)

    for key in ('_filename', 'filename'):
        path = info_dict.get(key)
        if path:
            candidates.append(path)

    if template_path:
        candidates.append(template_path)

    prepared_name = ydl_instance.prepare_filename(info_dict)
    candidates.append(prepared_name)

    base, _ = os.path.splitext(prepared_name)

    possible_exts = []
    ext = info_dict.get('ext')
    if ext:
        possible_exts.append(ext)

    possible_exts.extend(['mp4', 'mkv', 'webm', 'm4a', 'mp3', 'opus'])

    for ext in possible_exts:
        if not ext:
            continue
        clean_ext = ext if ext.startswith('.') else f'.{ext}'
        candidates.append(base + clean_ext)

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, (dict, list)):
            continue
        # Convert non-string candidates (e.g., Path objects, ints) to string
        try:
            candidate_str = os.fspath(candidate)
        except TypeError:
            candidate_str = str(candidate)

        if candidate_str and os.path.exists(candidate_str):
            return candidate_str

    return None
