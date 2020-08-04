# -*- mode: python -*-

block_cipher = None


a = Analysis(['dstimer_server.py'],
             pathex=['.'],
             binaries=None,
             datas=[
                ('dstimer/templates/*.html', 'dstimer/templates'),
                ('dstimer/static/*', 'dstimer/static')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
a.datas.append(('cacert.pem', 'cacert.pem', 'DATA'))
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='dstimer_server',
          debug=False,
          strip=False,
          upx=True,
          console=True,
          icon='dstimer/static/crow.ico' )