"""
sysres.py == system_resources
Module for dealing with system resoureces in the context of IBEIS
but without the need for an actual IBEIS Controller

"""
from __future__ import absolute_import, division, print_function
import os
from os.path import exists, join, realpath
import utool
import utool as ut
from six.moves import input, zip, map
from utool import util_cache, util_list
from ibeis import constants as const
from ibeis import params

# Inject utool functions
(print, rrr, profile) = utool.inject2(__name__, '[sysres]')

WORKDIR_CACHEID   = 'work_directory_cache_id'
DEFAULTDB_CAHCEID = 'cached_dbdir'
LOGDIR_CACHEID = utool.logdir_cacheid
__APPNAME__ = 'ibeis'


def get_ibeis_resource_dir():
    return ut.ensure_app_resource_dir('ibeis')


def _ibeis_cache_dump():
    util_cache.global_cache_dump(appname=__APPNAME__)


def _ibeis_cache_write(key, val):
    """ Writes to global IBEIS cache """
    print('[sysres] set %s=%r' % (key, val))
    util_cache.global_cache_write(key, val, appname=__APPNAME__)


def _ibeis_cache_read(key, **kwargs):
    """ Reads from global IBEIS cache """
    return util_cache.global_cache_read(key, appname=__APPNAME__, **kwargs)


# Specific cache getters / setters

def set_default_dbdir(dbdir):
    """
    """
    if ut.DEBUG2:
        print('[sysres] SETTING DEFAULT DBDIR: %r' % dbdir)
    _ibeis_cache_write(DEFAULTDB_CAHCEID, dbdir)


def get_default_dbdir():
    dbdir = _ibeis_cache_read(DEFAULTDB_CAHCEID, default=None)
    if ut.DEBUG2:
        print('[sysres] READING DEFAULT DBDIR: %r' % dbdir)
    return dbdir


def get_workdir(allow_gui=True):
    """
    Returns the work directory set for this computer.  If allow_gui is true,
    a dialog will ask a user to specify the workdir if it does not exist.

    python -c "import ibeis; print(ibeis.get_workdir())"

    Args:
        allow_gui (bool): (default = True)

    Returns:
        str: work_dir

    CommandLine:
        python -m ibeis.init.sysres --exec-get_workdir

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> allow_gui = True
        >>> work_dir = get_workdir(allow_gui)
        >>> result = ('work_dir = %s' % (str(work_dir),))
        >>> print(result)
    """
    work_dir = _ibeis_cache_read(WORKDIR_CACHEID, default='.')
    if work_dir is not '.' and exists(work_dir):
        return work_dir
    if allow_gui:
        work_dir = set_workdir()
        return get_workdir(allow_gui=False)
    return None


ALLOW_GUI = ut.WIN32 or os.environ.get('DISPLAY', None) is not None


def set_workdir(work_dir=None, allow_gui=ALLOW_GUI):
    """ Sets the workdirectory for this computer

    Args:
        work_dir (None): (default = None)
        allow_gui (bool): (default = True)

    CommandLine:
        python -c "import ibeis; ibeis.sysres.set_workdir('/raid/work2')"
        python -c "import ibeis; ibeis.sysres.set_workdir('/raid/work')"

        python -m ibeis.init.sysres --exec-set_workdir --workdir

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> print('current_work_dir = %s' % (str(get_workdir(False)),))
        >>> work_dir = ut.get_argval('--workdir', type_=str, default=None)
        >>> allow_gui = True
        >>> result = set_workdir(work_dir, allow_gui)
    """
    if work_dir is None:
        if allow_gui:
            try:
                work_dir = guiselect_workdir()
            except ImportError:
                allow_gui = False
        if not allow_gui:
            work_dir = ut.truepath(input('specify a workdir: '))
    if work_dir is None or not exists(work_dir):
        raise AssertionError('invalid workdir=%r' % work_dir)
    _ibeis_cache_write(WORKDIR_CACHEID, work_dir)


def set_logdir(log_dir):
    from os.path import realpath, expanduser
    log_dir = realpath(expanduser(log_dir))
    utool.ensuredir(log_dir, verbose=True)
    utool.stop_logging()
    _ibeis_cache_write(LOGDIR_CACHEID, log_dir)
    utool.start_logging(appname=__APPNAME__)


def get_logdir():
    return _ibeis_cache_read(LOGDIR_CACHEID, default=ut.get_logging_dir(appname='ibeis'))


def get_rawdir():
    """ Returns the standard raw data directory """
    workdir = get_workdir()
    rawdir = utool.truepath(join(workdir, '../raw'))
    return rawdir


def guiselect_workdir():
    """ Prompts the user to specify a work directory """
    import guitool
    guitool.ensure_qtapp()
    # Gui selection
    work_dir = guitool.select_directory('Select a work directory')

    # Make sure selection is ok
    if not exists(work_dir):
        try_again = guitool.user_option(
            paremt=None,
            msg='Directory %r does not exist.' % work_dir,
            title='get work dir failed',
            options=['Try Again'],
            use_cache=False)
        if try_again == 'Try Again':
            return guiselect_workdir()
    return work_dir


def get_dbalias_dict():
    dbalias_dict = {}
    if utool.is_developer():
        # For jon's convinience
        dbalias_dict.update({
            'NAUTS':            'NAUT_Dan',
            'WD':               'WD_Siva',
            'LF':               'LF_all',
            'GZ':               'GZ_ALL',
            'MOTHERS':          'PZ_MOTHERS',
            'FROGS':            'Frogs',
            'TOADS':            'WY_Toads',
            'SEALS_SPOTTED':    'Seals',

            'OXFORD':           'Oxford_Buildings',
            'PARIS':            'Paris_Buildings',

            'JAG_KELLY':        'JAG_Kelly',
            'JAG_KIERYN':       'JAG_Kieryn',
            'WILDEBEAST':       'Wildebeast',
            'WDOGS':            'WD_Siva',

            'PZ':               'PZ_FlankHack',
            'PZ2':              'PZ-Sweatwater',
            'PZ_MARIANNE':      'PZ_Marianne',
            'PZ_DANEXT_TEST':   'PZ_DanExt_Test',
            'PZ_DANEXT_ALL':    'PZ_DanExt_All',

            'LF_ALL':           'LF_all',
            'WS_HARD':          'WS_hard',
            'SONOGRAMS':        'sonograms',

        })
        dbalias_dict['JAG'] = dbalias_dict['JAG_KELLY']
    return dbalias_dict


def db_to_dbdir(db, allow_newdir=False, extra_workdirs=[], use_sync=False):
    """ Implicitly gets dbdir. Searches for db inside of workdir """
    if utool.VERBOSE:
        print('[sysres] db_to_dbdir: db=%r, allow_newdir=%r' % (db, allow_newdir))

    work_dir = get_workdir()
    dbalias_dict = get_dbalias_dict()

    workdir_list = []
    for extra_dir in extra_workdirs:
        if exists(extra_dir):
            workdir_list.append(extra_dir)
    if use_sync:
        sync_dir = join(work_dir, '../sync')
        if exists(sync_dir):
            workdir_list.append(sync_dir)
    workdir_list.append(work_dir)  # TODO: Allow multiple workdirs

    # Check all of your work directories for the database
    for _dir in workdir_list:
        dbdir = realpath(join(_dir, db))
        # Use db aliases
        if not exists(dbdir) and db.upper() in dbalias_dict:
            dbdir = join(_dir, dbalias_dict[db.upper()])
        if exists(dbdir):
            break

    # Create the database if newdbs are allowed in the workdir
    #print('allow_newdir=%r' % allow_newdir)
    if allow_newdir:
        utool.ensuredir(dbdir, verbose=True)

    # Complain if the implicit dbdir does not exist
    if not exists(dbdir):
        print('!!!')
        print('[sysres] WARNING: db=%r not found in work_dir=%r' %
              (db, work_dir))
        fname_list = os.listdir(work_dir)
        lower_list = [fname.lower() for fname in fname_list]
        index = util_list.listfind(lower_list, db.lower())
        if index is not None:
            print('[sysres] WARNING: db capitalization seems to be off')
            if not utool.STRICT:
                print('[sysres] attempting to fix it')
                db = fname_list[index]
                dbdir = join(work_dir, db)
                print('[sysres] dbdir=%r' % dbdir)
                print('[sysres] db=%r' % db)
        if not exists(dbdir):
            msg = '[sysres!] ERROR: Database does not exist and allow_newdir=False'
            print('<!!!>')
            print(msg)
            print('[sysres!] Here is a list of valid dbs: ' +
                  utool.indentjoin(sorted(fname_list), '\n  * '))
            print('[sysres!] dbdir=%r' % dbdir)
            print('[sysres!] db=%r' % db)
            print('[sysres!] work_dir=%r' % work_dir)
            print('</!!!>')
            raise AssertionError(msg)
        print('!!!')
    return dbdir


def get_args_dbdir(defaultdb=None, allow_newdir=False, db=None, dbdir=None,
                   cache_priority=False):
    """ Machinery for finding a database directory

    such a hacky function with bad coding.
    Needs to just return a database dir and use the following priority
    dbdir, db, cache, something like that...
    """
    if not utool.QUIET and utool.VERBOSE:
        print('[sysres] get_args_dbdir: parsing commandline for dbdir')
        print('[sysres] defaultdb=%r, allow_newdir=%r, cache_priority=%r' % (defaultdb, allow_newdir, cache_priority))
        print('[sysres] db=%r, dbdir=%r' % (db, dbdir))

    if ut.get_argflag('--nodbcache'):
        return dbdir

    def _db_arg_priorty(dbdir_, db_):
        invalid = ['', ' ', '.', 'None']
        # Invalidate bad db's
        if dbdir_ in invalid:
            dbdir_ = None
        if db_ in invalid:
            db_ = None
        # Return values with a priority
        if dbdir_ is not None:
            return realpath(dbdir_)
        if db_ is not None:
            return db_to_dbdir(db_, allow_newdir=allow_newdir)
        return None

    if not cache_priority:
        # Check function's passed args
        dbdir = _db_arg_priorty(dbdir, db)
        if dbdir is not None:
            return dbdir
        # Get command line args
        dbdir = params.args.dbdir
        db = params.args.db
        # TODO; use these instead of params
        #ut.get_argval('--dbdir', return_was_specified=True))
        #ut.get_argval('--db', return_was_specified=True)
        # Check command line passed args
        dbdir = _db_arg_priorty(dbdir, db)
        if dbdir is not None:
            return dbdir
    # Return cached database directory
    if defaultdb == 'cache':
        return get_default_dbdir()
    else:
        return db_to_dbdir(defaultdb, allow_newdir=allow_newdir)


def resolve_dbdir2(defaultdb=None, allow_newdir=False, db=None, dbdir=None):
    r"""

    CommandLine:
        python -m ibeis.init.sysres --exec-resolve_dbdir2 --db PZ_MTEST
        python -m ibeis.init.sysres --exec-resolve_dbdir2 --db None
        python -m ibeis.init.sysres --exec-resolve_dbdir2 --dbdir None

    Args:
        defaultdb (None): (default = None)
        allow_newdir (bool): (default = False)
        db (None): (default = None)
        dbdir (None): (default = None)

    CommandLine:
        python -m ibeis.init.sysres --exec-resolve_dbdir2

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> defaultdb = 'cache'
        >>> allow_newdir = False
        >>> dbdir_ = resolve_dbdir2(defaultdb)
        >>> result = ('dbdir_ = %r' % (dbdir_,))
        >>> print(result)
    """
    invalid = ['', ' ', '.', 'None']
    if db in invalid:
        db = None
    if dbdir in invalid:
        dbdir = None
    db, db_specified = ut.get_argval(
        '--db', type_=str, default=db, return_was_specified=True)
    dbdir, dbdir_specified = ut.get_argval(
        '--dbdir', type_=str, default=dbdir, return_was_specified=True)

    dbdir_flag = dbdir_specified or dbdir is not None
    db_flag = db_specified or db is not None

    if dbdir_flag:
        # Priority 1
        dbdir_ = realpath(dbdir)
    elif db_flag:
        # Priority 2
        dbdir_ = db_to_dbdir(db, allow_newdir=allow_newdir)
    else:
        # Priority 3
        if defaultdb == 'cache':
            dbdir_ = get_default_dbdir()
        else:
            dbdir_ = db_to_dbdir(defaultdb, allow_newdir=allow_newdir)
    return dbdir_


def is_ibeisdb(path):
    """ Checks to see if path contains the IBEIS internal dir """
    return exists(join(path, const.PATH_NAMES._ibsdb))


def get_ibsdb_list(workdir=None):
    r"""
    Lists the available valid ibeis databases inside of a work directory

    Args:
        workdir (None):

    Returns:
        IBEISController: ibsdb_list -  ibeis controller object

    CommandLine:
        python -m ibeis.init.sysres --test-get_ibsdb_list

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> workdir = None
        >>> ibsdb_list = get_ibsdb_list(workdir)
        >>> result = str('\n'.join(ibsdb_list))
        >>> print(result)
    """
    import numpy as np
    if workdir is None:
        workdir = get_workdir()
    dbname_list = os.listdir(workdir)
    dbpath_list = np.array([join(workdir, name) for name in dbname_list])
    is_ibs_list = np.array(list(map(is_ibeisdb, dbpath_list)))
    ibsdb_list  = dbpath_list[is_ibs_list].tolist()
    return ibsdb_list


def ensure_pz_mtest():
    """
    Ensures that you have the PZ_MTEST dataset

    Example:
        >>> # DISABLE DOCTEST
        >>> pass
    """
    from ibeis import sysres
    import utool
    workdir = sysres.get_workdir()
    mtest_zipped_url = const.ZIPPED_URLS.PZ_MTEST
    mtest_dir = utool.grab_zipped_url(mtest_zipped_url, ensure=True, download_dir=workdir)
    print('have mtest_dir=%r' % (mtest_dir,))
    # update the the newest database version
    import ibeis
    ibs = ibeis.opendb('PZ_MTEST')
    print('cleaning up old database and ensureing everything is properly computed')
    ibs.db.vacuum()
    valid_aids = ibs.get_valid_aids()
    assert len(valid_aids) == 119
    ibs.update_annot_semantic_uuids(valid_aids)
    if ut.VERYVERBOSE:
        ibs.print_annotation_table()
    nid = ibs.get_name_rowids_from_text('', ensure=False)
    if nid is not None:
        ibs.set_name_texts([nid], ['lostname'])


def copy_ibeisdb(source_dbdir, dest_dbdir):
    # TODO; rectify with rsycn script
    from os.path import normpath
    import ibeis
    exclude_dirs = [ut.ensure_unixslash(normpath(rel)) for rel in ibeis.const.EXCLUDE_COPY_REL_DIRS + ['_hsdb', '.hs_internals']]

    rel_tocopy = ut.glob(source_dbdir, '*', exclude_dirs=exclude_dirs, recursive=True, with_files=True, with_dirs=False, fullpath=False)
    rel_tocopy_dirs = ut.glob(source_dbdir, '*', exclude_dirs=exclude_dirs, recursive=True, with_files=False, with_dirs=True, fullpath=False)

    src_list = [join(source_dbdir, relpath) for relpath in rel_tocopy]
    dst_list = [join(dest_dbdir, relpath) for relpath in rel_tocopy]

    # ensure directories exist
    rel_tocopy_dirs = [dest_dbdir] + [join(dest_dbdir, dpath_) for dpath_ in rel_tocopy_dirs]
    for dpath in rel_tocopy_dirs:
        ut.ensuredir(dpath)
    # copy files
    ut.copy(src_list, dst_list)


def ensure_pz_mtest_batchworkflow_test():
    r"""
    CommandLine:
        python -m ibeis.init.sysres --test-ensure_pz_mtest_batchworkflow_test
        python -m ibeis.init.sysres --test-ensure_pz_mtest_batchworkflow_test --reset
        python -m ibeis.init.sysres --test-ensure_pz_mtest_batchworkflow_test --reset

    Example:
        >>> # SCRIPT
        >>> from ibeis.init.sysres import *  # NOQA
        >>> ensure_pz_mtest_batchworkflow_test()
    """
    import ibeis
    ibeis.ensure_pz_mtest()
    workdir = ibeis.sysres.get_workdir()
    mtest_dbpath = join(workdir, 'PZ_MTEST')

    source_dbdir = mtest_dbpath
    dest_dbdir = join(workdir, 'PZ_BATCH_WORKFLOW_MTEST')

    if ut.get_argflag('--reset'):
        ut.delete(dest_dbdir)

    if ut.checkpath(dest_dbdir):
        return
    else:
        copy_ibeisdb(source_dbdir, dest_dbdir)

    ibs = ibeis.opendb('PZ_BATCH_WORKFLOW_MTEST')
    assert len(ibs.get_valid_aids()) == 119
    assert len(ibs.get_valid_nids()) == 41

    ibs.delete_all_encounters()

    aid_list = ibs.get_valid_aids()

    unixtime_list = ibs.get_annot_image_unixtimes(aid_list)
    untimed_aids = ut.list_compress(aid_list, [t == -1 for t in unixtime_list])

    ibs.get_annot_groundtruth(untimed_aids, aid_list)

    aids_list, nid_list = ibs.group_annots_by_name(aid_list)

    hourdiffs_list = ibs.get_name_hourdiffs(nid_list)

    encounter_aids_list = [[] for _ in range(4)]

    encounter_idx = 0

    for hourdiffs, aids in zip(hourdiffs_list, aids_list):
        #import scipy.spatial.distance as spdist
        if len(aids) == 1:
            encounter_aids_list[encounter_idx].extend(aids)
            encounter_idx = (encounter_idx + 1) % len(encounter_aids_list)
        else:
            for chunk in list(ut.ichunks(aids, 2)):
                encounter_aids_list[encounter_idx].extend(chunk)
                encounter_idx = (encounter_idx + 1) % len(encounter_aids_list)

            #import vtool as vt
            #import networkx as netx
            #nodes = list(range(len(aids)))
            #edges_pairs = vt.pdist_argsort(hourdiffs)
            #edge_weights = -hourdiffs[hourdiffs.argsort()]
            #netx_graph = make_netx_graph(edges_pairs, nodes, edge_weights)
            #cut_edges = netx.minimum_edge_cut(netx_graph)
            #netx_graph.remove_edges_from(cut_edges)
            #components = list(netx.connected_components(netx_graph))
            #components = ut.sortedby(components, list(map(len, components)), reverse=True)
            #print(components)
            #encounter_aids_list[0].extend(components[0])
            #for compoment in components:

            # TODO do max-nway cut
        #day_diffs = spdist.squareform(hourdiffs) / 24.0
        #print(ut.numpy_str(day_diffs, precision=2, suppress_small=True))
        #import itertools
        #compare_idxs = [(r, c) for r, c in itertools.product(range(len(aids)), range(len(aids))) if (c > r)]
        #print(len(aids))
    #def make_netx_graph(edges_pairs, nodes=None, edge_weights=None):
    #    import networkx as netx
    #    node_lbls = [('id_', 'int')]

    #    edge_lbls = [('weight', 'float')]
    #    edges = [(pair[0], pair[1], weight) for pair, weight in zip(edges_pairs, edge_weights)]

    #    print('make_netx_graph')
    #    # Make a graph between the chips
    #    netx_nodes = [(ntup[0], {key[0]: val for (key, val) in zip(node_lbls, ntup[1:])})
    #                  for ntup in iter(zip(nodes))]

    #    netx_edges = [(etup[0], etup[1], {key[0]: val for (key, val) in zip(edge_lbls, etup[2:])})
    #                  for etup in iter(edges)]
    #    netx_graph = netx.Graph()
    #    netx_graph.add_nodes_from(netx_nodes)
    #    netx_graph.add_edges_from(netx_edges)
    #    return netx_graph

    # Group into encounters based on old names
    gids_list = ibs.unflat_map(ibs.get_annot_image_rowids, encounter_aids_list)
    eid_list = ibs.new_encounters_from_images(gids_list)  # NOQA

    # Remove all names
    ibs.delete_annot_nids(aid_list)


def ensure_pz_mtest_mergesplit_test():
    r"""
    Make a test database for MERGE and SPLIT cases

    CommandLine:
        python -m ibeis.init.sysres --test-ensure_pz_mtest_mergesplit_test

    Example:
        >>> # SCRIPT
        >>> from ibeis.init.sysres import *  # NOQA
        >>> ensure_pz_mtest_mergesplit_test()
    """
    import ibeis
    ibeis.ensure_pz_mtest()
    workdir = ibeis.sysres.get_workdir()
    mtest_dbpath = join(workdir, 'PZ_MTEST')

    source_dbdir = mtest_dbpath
    dest_dbdir = join(workdir, 'PZ_MERGESPLIT_MTEST')

    if ut.get_argflag('--reset'):
        ut.delete(dest_dbdir)
    if ut.checkpath(dest_dbdir):
        return

    copy_ibeisdb(source_dbdir, dest_dbdir)

    ibs = ibeis.opendb('PZ_MERGESPLIT_MTEST')
    assert len(ibs.get_valid_aids()) == 119
    assert len(ibs.get_valid_nids()) == 41

    aid_list = ibs.get_valid_aids()
    aids_list, nid_list = ibs.group_annots_by_name(aid_list)
    num_aids = list(map(len, aids_list))

    # num cases wanted
    num_merge = 3
    num_split = 1
    num_combo = 1

    # num inputs needed
    num_merge_names = num_merge
    num_split_names = num_split * 2
    num_combo_names = num_combo * 3

    total_names = num_merge_names + num_split_names + num_combo_names

    modify_aids = ut.list_take(aids_list, ut.list_argsort(num_aids, reverse=True)[0:total_names])

    merge_nids1 = ibs.make_next_nids(num_merge, location_text='XMERGE')
    merge_nids2 = ibs.make_next_nids(num_merge, location_text='XMERGE')
    split_nid  = ibs.make_next_nids(num_split, location_text='XSPLIT')[0]
    combo_nids = ibs.make_next_nids(num_combo * 2, location_text='XCOMBO')

    # the first 3 become merge cases
    #left = 0
    #right = left + num_merge
    for aids, nid1, nid2 in zip(modify_aids[0:3], merge_nids1, merge_nids2):
        #ibs.get_annot_nids(aids)
        aids_ = aids[::2]
        ibs.set_annot_name_rowids(aids_, [nid1] * len(aids_))
        ibs.set_annot_name_rowids(aids_, [nid2] * len(aids_))

    # the next 2 become split cases
    #left = right
    #right = left + num_split_names
    for aids in modify_aids[3:5]:
        ibs.set_annot_name_rowids(aids, [split_nid] * len(aids))

    #left = right
    #right = left + num_combo_names
    # The final 3 are a combination case
    for aids in modify_aids[5:8]:
        aids_even = aids[::2]
        aids_odd = aids[1::2]
        ibs.set_annot_name_rowids(aids_even, [combo_nids[0]] * len(aids_even))
        ibs.set_annot_name_rowids(aids_odd, [combo_nids[1]] * len(aids_odd))

    final_result = ibs.unflat_map(ibs.get_annot_nids, modify_aids)
    print('final_result = %s' % (ut.list_str(final_result),))


def ensure_nauts():
    """ Ensures that you have the NAUT_test dataset """
    from ibeis import sysres
    import utool
    workdir = sysres.get_workdir()
    nauts_zipped_url = const.ZIPPED_URLS.NAUTS
    nauts_dir = utool.grab_zipped_url(nauts_zipped_url, ensure=True, download_dir=workdir)
    print('have nauts_dir=%r' % (nauts_dir,))


def get_global_distinctiveness_modeldir(ensure=True):
    resource_dir = get_ibeis_resource_dir()
    global_distinctdir = join(resource_dir, const.PATH_NAMES.distinctdir)
    if ensure:
        ut.ensuredir(global_distinctdir)
    return global_distinctdir


def resolve_species(species_code):
    r"""
    Args:
        species_code (str): can either be species_code or species_text

    CommandLine:
        python -m ibeis.init.sysres --test-resolve_species

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.init.sysres import *  # NOQA
        >>> # build test data
        >>> species = 'GZ'
        >>> # execute function
        >>> result = resolve_species(species)
        >>> # verify results
        >>> print(result)
        zebra_grevys
    """
    species_text = const.SPECIES_CODE_TO_TEXT.get(species_code.upper(), species_code).lower()
    assert species_text in const.VALID_SPECIES, 'cannot resolve species_text=%r' % (species_text,)
    return species_text


def grab_example_smart_xml_fpath():
    """ Gets smart example xml

    CommandLine:
        python -m ibeis.init.sysres --test-grab_example_smart_xml_fpath

    Example:
        >>> # DISABLE_DOCTEST
        >>> import ibeis
        >>> import utool as ut
        >>> import os
        >>> smart_xml_fpath = ibeis.sysres.grab_example_smart_xml_fpath()
        >>> os.system('gvim ' + smart_xml_fpath)
        >>> #ut.editfile(smart_xml_fpath)

    """
    import utool
    smart_xml_url = 'https://www.dropbox.com/s/g1mpjzp57wfnhk6/LWC_000261.xml'
    smart_sml_fpath = utool.grab_file_url(smart_xml_url, ensure=True, appname='ibeis')
    return smart_sml_fpath


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.init.sysres
        python -m ibeis.init.sysres --allexamples
        python -m ibeis.init.sysres --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
