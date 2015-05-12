import os, sys, subprocess, time, traceback, types, datetime
import wasanbon
from wasanbon.core.plugins import PluginFunction, manifest

report_file_name = 'build_report.yaml'
test_package_name = 'build_test_package'
test_rtc_name = None
exclusive_rtc_repo = ['LEDTest']

class Plugin(PluginFunction):

    def __init__(self):
        #PluginFunction.__init__(self)
        super(Plugin, self).__init__()
        pass

    def depends(self):
        return ['admin.environment']

    @manifest
    def allbuild(self, argv):
        """ Build-Test All RTCs in Binder """
        self.parser.add_option('-p', '--package', help='Package Name (default=build_test_package)', default='build_test_package', action='store', dest='package_name')
        options, argv = self.parse_args(argv[:])
        verbose = options.verbose_flag # This is default option
        #force   = options.force_flag
        wasanbon.arg_check(argv, 4)
        
        global test_package_name
        test_package_name = options.package_name
        global test_rtc_name
        test_rtc_name = []
        for arg in argv[3:]:
            test_rtc_name = test_rtc_name + [arg]
        if 'all' in test_rtc_name:
            test_rtc_name = None
        
        return main()



def check_output(cmd):
    print 'CMD:', cmd
    #if cmd[0].endswith('.py'):
    #    cmd = ['python'] + cmd
    if sys.platform == 'win32' and cmd[0].startswith('./'):
        cmd[0] = cmd[0][2:]

    #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)
    p.wait()
    output = p.stdout.read()
    return output

def call(cmd):
    print 'CMD:', cmd
    if sys.platform == 'win32' and cmd[0].startswith('./'):
        cmd[0] = cmd[0][2:]
    #if cmd[0].endswith('.py'):
    #    cmd = ['python'] + cmd
    #p = subprocess.call(cmd, shell=True)
    p = subprocess.call(cmd, shell=False)
    return p

def main():
    import yaml
    build_status_dir = {}
    global report_file_name, test_package_name

    # Refresh test build package
    output = check_output(['wasanbon-admin.py', 'package', 'list'])
    pack_names = yaml.load(output)

    if test_package_name in pack_names:
        #subprocess.call(['wasanbon-admin.py', 'package', 'unregister', test_package_name, '-c'])
        pass
    else:
        call(['wasanbon-admin.py', 'package', 'create', test_package_name, '-v'])

    report_file_path = os.path.join(test_package_name, report_file_name)
    if os.path.isfile(report_file_path):
        os.rename(report_file_path, report_file_path + wasanbon.timestampstr())
    report_file = open(report_file_path, "w")
    
    dirname = check_output(['wasanbon-admin.py', 'package', 'directory', test_package_name])
    if type(dirname) == types.StringType:
        dirname = dirname.strip()
    org_dir = os.getcwd()
    os.chdir(dirname.strip())

    output = check_output(['./mgr.py', 'rtc', 'list'])
    rtc_names = yaml.load(output)
    if type(rtc_names) == types.ListType:
        for rtc_name in rtc_names:
            if not rtc_name in exclusive_rtc_repo:
                if test_rtc_name:
                    if not rtc_name in test_rtc_name:
                        continue
                ret = call(['./mgr.py', 'repository', 'pull', rtc_name])
    else:
        rtc_names = []

        output = check_output(['./mgr.py', 'repository', 'list'])
        rtc_repo_names = yaml.load(output)
        for rtc_repo_name in rtc_repo_names:
            if rtc_repo_name in exclusive_rtc_repo:
                continue
            if test_rtc_name:
                if not rtc_repo_name in test_rtc_name:
                    continue
            call(['./mgr.py', 'rtc', 'clone', rtc_repo_name])
            pass
        pass

    output = check_output(['./mgr.py', 'rtc', 'list'])
    rtc_names = yaml.load(output)
    for rtc_name in rtc_names:
        if test_rtc_name:
            if not rtc_name in test_rtc_name:
                continue
        ret = call(['./mgr.py', 'rtc', 'build', rtc_name])
        build_status_dir[rtc_name] = {'status' : ret, 'date' : str(datetime.datetime.now())}

    report_file.write(yaml.dump(build_status_dir))
    report_file.close()

    os.chdir(org_dir)
    # subprocess.call(['wasanbon-admin.py', 'package', 'unregister', test_package_name, '-c'])

    return 0
        
