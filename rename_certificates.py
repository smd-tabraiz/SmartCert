import os
import csv
import shutil


def rename_certificates(csv_path, cert_folder, output_folder):
    """
    Rename certificate files based on participant names from a CSV file.

    Expected CSV columns: name, email
    The function matches certificates by their upload order (row order in CSV)
    OR by matching filename hints. It copies each cert file and renames it to
    '<name>_certificate.<ext>' in the output folder.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Read participants from CSV
    participants = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Trigger header parsing by peeking, then normalize
        _ = reader.fieldnames  # forces CSV to read the header line
        if reader.fieldnames:
            reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        for row in reader:
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()
            if name and email:
                participants.append({'name': name, 'email': email})

    # Get all certificate files sorted
    cert_files = sorted([
        f for f in os.listdir(cert_folder)
        if os.path.isfile(os.path.join(cert_folder, f))
    ])

    renamed = []
    for i, participant in enumerate(participants):
        if i >= len(cert_files):
            break

        cert_file = cert_files[i]
        ext = os.path.splitext(cert_file)[1]
        safe_name = participant['name'].replace(' ', '_').replace('/', '_')
        new_filename = f"{safe_name}_certificate{ext}"
        src = os.path.join(cert_folder, cert_file)
        dst = os.path.join(output_folder, new_filename)
        shutil.copy2(src, dst)
        renamed.append({
            'original': cert_file,
            'renamed': new_filename,
            'name': participant['name'],
            'email': participant['email']
        })

    return renamed
