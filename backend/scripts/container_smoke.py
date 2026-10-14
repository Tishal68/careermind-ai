"""Run against the built unified image. No AI service or real user data required."""
import io
import os
import secrets
import time
import httpx
from docx import Document

base = os.environ.get('SMOKE_URL', 'http://127.0.0.1:10000') + '/api/v1'
with httpx.Client(timeout=30) as client:
    for attempt in range(90):
        try:
            if client.get(base+'/ready').status_code == 200: break
        except httpx.HTTPError: pass
        time.sleep(2)
    else: raise AssertionError('Container did not become ready')
    password=secrets.token_urlsafe(24)
    email='container-'+secrets.token_hex(8)+'@example.com'
    registered=client.post(base+'/auth/register',json={'email':email,'password':password,'full_name':'Container smoke'})
    assert registered.status_code==201, registered.status_code
    login=client.post(base+'/auth/login',json={'email':email,'password':password})
    assert login.status_code==200
    headers={'Authorization':'Bearer '+login.json()['access_token']}
    doc=Document();doc.add_paragraph('Python SQL backend developer with testing experience.');data=io.BytesIO();doc.save(data)
    # Minimal real text PDF, generated without an additional dependency.
    stream=b'BT /F1 12 Tf 40 750 Td (Python SQL developer resume) Tj ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    pdf=b'%PDF-1.4\n'; offsets=[0]
    for index, obj in enumerate(objects,1):offsets.append(len(pdf));pdf+=str(index).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
    xref=len(pdf);pdf+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF'
    for name,content in [('resume.docx',data.getvalue()),('resume.pdf',pdf)]:
        uploaded=client.post(base+'/resume/upload',headers=headers,files={'file':(name,content)})
        assert uploaded.status_code==201, (name,uploaded.status_code,uploaded.text[:200])
        assert 'Python' in uploaded.json()['parsed_data']['technical_skills']
        assert client.delete(base+'/resume/session/'+str(uploaded.json()['id']),headers=headers).status_code==204
    assert client.post(base+'/auth/logout',headers=headers).status_code==204
    assert client.get(base+'/auth/me',headers=headers).status_code==401
print('PASS: container readiness, registration, login, DOCX/PDF worker, deletion, revoked logout')
