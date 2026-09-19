"""Build the local native observer shell from an explicitly supplied reviewed frame source."""
from pathlib import Path
import argparse,hashlib,json,plistlib,shutil,subprocess
from import_standing import verify_package, BASE_SHA

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--icon',type=Path,required=True)
    p.add_argument('--annoyed',type=Path,required=True,help='Reviewed transparent frown/anger-mark PNG')
    p.add_argument('--standing',type=Path,required=True,help='Approved exact standing-loop package from import_standing.py')
    p.add_argument('--work-tier-2',type=Path,help='Approved exact 596px task_2 work-eating package')
    p.add_argument('--work-tier-3',type=Path,help='Visually approved exact 596px task_3 static work-eating package')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--slouch',type=Path,help='Reviewed optional double-cheek package')
    p.add_argument('--sleep',type=Path,help='Selected static sleep package, preview only')
    p.add_argument('--sleep-chain',action='store_true',help='Use five-pose compressed preview with --sleep; never production')
    p.add_argument('--preview',action='store_true',help='Separate preview app identity and preferences; never replaces the installed app')
    a=p.parse_args();source=a.source.resolve();app=a.out.resolve()
    assert not app.exists(), 'Refuse to overwrite a built app'
    assert source not in app.parents and app not in source.parents
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    expected='e622ed0123ece85248f82d2b08476e03a81c2e0eeb2e32304834d679f7457da8'
    assert sha(source/'source.json')==expected
    manifest=json.loads((source/'source.json').read_text())
    for record in [manifest['base']]+manifest['frames']:
        assert sha(source/record['file'])==record['sha256']
    reaction_sha='314f34dcb6d5dbba04555f5996ec3f612e0dc65e7f0c080a027eee1093ccbd3f'
    assert sha(a.annoyed)==reaction_sha, 'Unreviewed annoyed artwork'
    verify_package(a.standing)
    assert a.standing.resolve() not in app.parents and app not in a.standing.resolve().parents
    if a.work_tier_2:
        tier2=a.work_tier_2.resolve()
        assert tier2 not in app.parents and app not in tier2.parents
        expected_tier2_manifest='81aa07c5503150f634a0b6e267f9621147f6f6a275e25b79b6c41e7ef1d447de'
        assert sha(tier2/'source.json')==expected_tier2_manifest, 'Unreviewed task_2 manifest'
        tm=json.loads((tier2/'source.json').read_text())
        assert tm['exact_frame_source_version']==1 and tm['character']=='reimu'
        assert tm['state_set']=='eating' and tm['state']=='task_2'
        assert tm['canvas']=={'width':596,'height':596}
        assert tm['playback']=={'fps':10,'frame_count':16,'loop':True}
        assert tm['base']=={'file':'base.png','sha256':'0251947e0ca94f0ba0fa4b724d37fac242c86ba4de9591bb558c226ad4904cfe'}
        assert len(tm['frames'])==16
        for i,record in enumerate(tm['frames']):
            assert record['file']==f'frames/frame_{i:03d}.png' and record['duration_ms']==100
            assert sha(tier2/record['file'])==record['sha256']
        assert tm['frames'][0]['sha256']==tm['base']['sha256']==tm['frames'][-1]['sha256']
    if a.work_tier_3:
        tier3=a.work_tier_3.resolve()
        assert tier3 not in app.parents and app not in tier3.parents
        expected_tier3_manifest='17909602578f8c961480f9d7aaf0fce19b732c859bb107dfdc05a28a197540bc'
        assert sha(tier3/'source.json')==expected_tier3_manifest, 'Unreviewed task_3 manifest'
        tm=json.loads((tier3/'source.json').read_text())
        assert tm['exact_frame_source_version']==1 and tm['character']=='reimu'
        assert tm['state_set']=='eating' and tm['state']=='task_3'
        assert tm['canvas']=={'width':596,'height':596}
        assert tm['playback']=={'fps':8,'frame_count':1,'loop':True}
        assert tm['base']=={'file':'base.png','sha256':'45c212c88bd39053bb351d5f7bdf8da5d1a95ca743c532232290288927a2a9ff'}
        assert tm['frames']==[{'file':'frames/frame_000.png','sha256':tm['base']['sha256'],'duration_ms':125}]
        assert sha(tier3/'base.png')==tm['base']['sha256']
        assert sha(tier3/'frames/frame_000.png')==tm['base']['sha256']
    if a.slouch:
        assert a.slouch.resolve() not in app.parents and app not in a.slouch.resolve().parents
        sm=json.loads((a.slouch/'source.json').read_text())
        assert sm['state_set']=='double_cheek_v1' and sm['state']=='idle_blink'
        assert sm['canvas']=={'width':596,'height':596} and sm['playback']=={'fps':20,'frame_count':140,'loop':True}
        assert len(sm['frames'])==140
        for i,record in enumerate(sm['frames']):
            assert record['file']==('poses/closed.png' if 128<=i<=132 else 'base.png')
            assert record['duration_ms']==50 and sha(a.slouch/record['file'])==record['sha256']
        assert sm['base']['file']=='base.png' and sha(a.slouch/'base.png')==sm['base']['sha256']
    assert not a.sleep_chain or a.sleep, '--sleep-chain requires --sleep'
    if a.sleep:
        assert a.preview, 'Sleep pose needs native visual review before production'
        assert a.sleep.resolve() not in app.parents and app not in a.sleep.resolve().parents
        sleep_sha='b05094adf0232c544f741408b7d6e969e49a6ea2c98fd60afa49244e96ecdb5a'
        assert sha(a.sleep/'base.png')==sleep_sha, 'Not the user-selected sleep pose'
        sm=json.loads((a.sleep/'source.json').read_text())
        assert sm['exact_frame_source_version']==1 and sm['character']=='reimu'
        assert sm['state_set']==('sleep_chain_panel_v2' if a.sleep_chain else 'sleep_table_selected_v1')
        assert sm['state']==('timing_preview' if a.sleep_chain else 'static_preview')
        assert sm['canvas']=={'width':1254,'height':1254}
        assert sm['playback']==({'fps':5,'frame_count':5,'loop':True} if a.sleep_chain else {'fps':1,'frame_count':1,'loop':True})
        assert sm['base']=={'file':'base.png','sha256':sleep_sha}
        paths=['base.png','poses/awake.png','poses/yawn.png','poses/drowsy.png','base.png'] if a.sleep_chain else ['base.png']
        assert sm['frames']==[{'file':f,'sha256':sha(a.sleep/f),'duration_ms':200 if a.sleep_chain else 1000} for f in paths]
    resources=app/'Contents/Resources';binary=app/'Contents/MacOS'
    binary.mkdir(parents=True);resources.mkdir()
    shutil.copytree(source,resources/'Pet',copy_function=shutil.copyfile)
    shutil.copytree(a.standing,resources/'Standing',copy_function=shutil.copyfile)
    verify_package(resources/'Standing')
    shutil.copyfile(a.icon,resources/'PetIcon.icns')
    (resources/'Reactions').mkdir()
    shutil.copyfile(a.annoyed,resources/'Reactions/annoyed.png')
    assert sha(resources/'Reactions/annoyed.png')==reaction_sha
    name='灵梦桌宠预览' if a.preview else '灵梦桌宠'
    info={'CFBundleIdentifier':'local.reimu.onigiri.preview' if a.preview else 'local.reimu.onigiri.desktop','CFBundleName':name,
          'CFBundleDisplayName':name,'CFBundleExecutable':'ReimuPet','CFBundlePackageType':'APPL',
          'CFBundleShortVersionString':'1.10','CFBundleVersion':'12','PetPreviewBuild':a.preview,'LSMinimumSystemVersion':'13.0',
          'LSUIElement':True,'NSHighResolutionCapable':True,'NSPrincipalClass':'NSApplication',
          'CFBundleIconFile':'PetIcon','PetBaseSHA256':sha(source/'base.png'),
          'PetManifestSHA256':expected,'PetAnnoyedSHA256':reaction_sha,
          'PetStandingBaseSHA256':BASE_SHA,'PetStandingManifestSHA256':sha(resources/'Standing/source.json'),
          'NSHumanReadableCopyright':'非官方东方同人，本地示例。'}
    if a.work_tier_2:
        shutil.copytree(a.work_tier_2,resources/'WorkEatingTier2',copy_function=shutil.copyfile)
        info.update(PetWorkTier2BaseSHA256=sha(resources/'WorkEatingTier2/base.png'),
                    PetWorkTier2ManifestSHA256=sha(resources/'WorkEatingTier2/source.json'))
    if a.work_tier_3:
        shutil.copytree(a.work_tier_3,resources/'WorkEatingTier3',copy_function=shutil.copyfile)
        info.update(PetWorkTier3BaseSHA256=sha(resources/'WorkEatingTier3/base.png'),
                    PetWorkTier3ManifestSHA256=sha(resources/'WorkEatingTier3/source.json'))
    if a.slouch:
        shutil.copytree(a.slouch,resources/'Slouch',copy_function=shutil.copyfile)
        info.update(PetSlouchBaseSHA256=sha(resources/'Slouch/base.png'),PetSlouchManifestSHA256=sha(resources/'Slouch/source.json'))
    if a.sleep:
        shutil.copytree(a.sleep,resources/'Sleep',copy_function=shutil.copyfile)
        info.update(PetSleepChainPreview=a.sleep_chain,PetSleepBaseSHA256=sha(resources/'Sleep/base.png'),PetSleepManifestSHA256=sha(resources/'Sleep/source.json'))
    (app/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    root=Path(__file__).parent
    subprocess.run(['xcrun','swiftc','-swift-version','5','-O','-target','arm64-apple-macosx13.0',
                    str(root/'main.swift'),str(root/'WorkStatus.swift'),str(root/'PetBehavior.swift'),str(root/'StatusBubble.swift'),'-o',str(binary/'ReimuPet'),
                    '-framework','AppKit','-framework','CryptoKit'],check=True)
    # Finder can tag a newly created .app even when copyfile preserved only bytes.
    # Remove only signing-incompatible metadata from this new output, never sources.
    subprocess.run(['xattr','-cr',str(app)],check=True)
    subprocess.run(['codesign','--force','--sign','-','--timestamp=none',str(app)],check=True)
    subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
    print(json.dumps({'app':str(app),'executable_sha256':sha(binary/'ReimuPet'),'source_sha256':expected}))

if __name__=='__main__':main()
