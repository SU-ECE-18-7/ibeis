# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
import six
#import six
import utool as ut
print, rrr, profile = ut.inject2(
    __name__, '[expt_harn]')


@six.add_metaclass(ut.ReloadingMetaclass)
class ResultMetadata(object):
    def __init__(metadata, fpath, autoconnect=False):
        """
        metadata_fpath = join(figdir, 'result_metadata.shelf')
        metadata = ResultMetadata(metadata_fpath)
        """
        metadata.fpath = fpath
        metadata.dimensions = ['query_cfgstr', 'qaid']
        metadata._shelf = None
        metadata.dictstore = None
        if autoconnect:
            metadata.connect()

    def connect(metadata):
        import shelve
        metadata._shelf = shelve.open(metadata.fpath)
        if 'dictstore' not in metadata._shelf:
            dictstore = ut.AutoVivification()
            metadata._shelf['dictstore'] = dictstore
        metadata.dictstore = metadata._shelf['dictstore']

    def clear(metadata):
        dictstore = ut.AutoVivification()
        metadata._shelf['dictstore'] = dictstore
        metadata.dictstore = metadata._shelf['dictstore']

    def __del__(metadata):
        metadata.close()

    def close(metadata):
        metadata._shelf.close()

    def write(metadata):
        metadata._shelf['dictstore'] = metadata.dictstore
        metadata._shelf.sync()

    def set_global_data(metadata, cfgstr, qaid, key, val):
        metadata.dictstore[cfgstr][qaid][key] = val

    def sync_test_results(metadata, testres):
        """ store all test results in the shelf """
        for cfgx in range(len(testres.cfgx2_qreq_)):
            cfgstr = testres.get_cfgstr(cfgx)
            qaids = testres.qaids
            cfgresinfo = testres.cfgx2_cfgresinfo[cfgx]
            for key, val_list in six.iteritems(cfgresinfo):
                for qaid, val in zip(qaids, val_list):
                    metadata.set_global_data(cfgstr, qaid, key, val)
        metadata.write()

    def get_cfgstr_list(metadata):
        cfgstr_list = list(metadata.dictstore.keys())
        return cfgstr_list

    def get_column_keys(metadata):
        unflat_colname_list = [
            [cols.keys() for cols in qaid2_cols.values()]
            for qaid2_cols in six.itervalues(metadata.dictstore)
        ]
        colname_list = ut.unique_keep_order(ut.flatten(ut.flatten(unflat_colname_list)))
        return colname_list

    def get_square_data(metadata, cfgstr=None):
        # can only support one config at a time right now
        if cfgstr is None:
            cfgstr = metadata.get_cfgstr_list()[0]
        qaid2_cols = metadata.dictstore[cfgstr]
        qaids = list(qaid2_cols.keys())
        col_name_list = ut.unique_keep_order(ut.flatten([cols.keys() for cols in qaid2_cols.values()]))
        #col_name_list = ['qx2_scoreexpdiff', 'qx2_gt_aid']
        #colname2_colvals = [None for colname in col_name_list]
        column_list = [
            [colvals.get(colname, None) for qaid, colvals in six.iteritems(qaid2_cols)]
            for colname in col_name_list]
        col_name_list = ['qaids'] + col_name_list
        column_list = [qaids] + column_list
        print('depth_profile(column_list) = %r' % (ut.depth_profile(column_list),))
        return col_name_list, column_list


def make_metadata_custom_api(metadata):
    r"""
    CommandLine:
        python -m ibeis.expt.experiment_drawing --test-make_metadata_custom_api --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.expt.experiment_drawing import *  # NOQA
        >>> import guitool
        >>> guitool.ensure_qapp()
        >>> metadata_fpath = '/media/raid/work/Elephants_drop1_ears/_ibsdb/figures/result_metadata.shelf'
        >>> metadata = test_result.ResultMetadata(metadata_fpath, autoconnect=True)
        >>> wgt = make_metadata_custom_api(metadata)
        >>> ut.quit_if_noshow()
        >>> wgt.show()
        >>> wgt.raise_()
        >>> guitool.qtapp_loop(wgt, frequency=100)
    """
    import guitool
    from guitool.__PYQT__ import QtCore

    class MetadataViewer(guitool.APIItemWidget):
        def __init__(wgt, parent=None, tblnice='Result Metadata Viewer', **kwargs):
            guitool.APIItemWidget.__init__(wgt, parent=parent, tblnice=tblnice, **kwargs)
            wgt.connect_signals_and_slots()

        @guitool.slot_(QtCore.QModelIndex)
        def _on_doubleclick(wgt, qtindex):
            print('[wgt] _on_doubleclick: ')
            col = qtindex.column()
            if wgt.api.col_edit_list[col]:
                print('do nothing special for editable columns')
                return
            model = qtindex.model()
            colname = model.get_header_name(col)
            if colname.endswith('fpath'):
                print('showing fpath')
                fpath = model.get_header_data(colname, qtindex)
                ut.startfile(fpath)

        def connect_signals_and_slots(wgt):
            #wgt.view.clicked.connect(wgt._on_click)
            wgt.view.doubleClicked.connect(wgt._on_doubleclick)
            #wgt.view.pressed.connect(wgt._on_pressed)
            #wgt.view.activated.connect(wgt._on_activated)

    guitool.ensure_qapp()
    #cfgstr_list = metadata
    col_name_list, column_list = metadata.get_square_data()

    # Priority of column names
    colname_priority = ['qaids', 'qx2_gt_rank', 'qx2_gt_timedelta',
                        'qx2_gf_timedelta',  'analysis_fpath',
                        'qx2_gt_raw_score', 'qx2_gf_raw_score']
    colname_priority += sorted(ut.setdiff_ordered(col_name_list, colname_priority))
    sortx = ut.priority_argsort(col_name_list, colname_priority)
    col_name_list = ut.take(col_name_list, sortx)
    column_list = ut.take(column_list, sortx)

    col_lens = list(map(len, column_list))
    print('col_name_list = %r' % (col_name_list,))
    print('col_lens = %r' % (col_lens,))
    assert len(col_lens) > 0, 'no columns'
    assert col_lens[0] > 0, 'no rows'
    assert all([len_ == col_lens[0] for len_ in col_lens]), 'inconsistant data'
    col_types_dict = {}
    col_getter_dict = dict(zip(col_name_list, column_list))
    col_bgrole_dict = {}
    col_ider_dict = {}
    col_setter_dict = {}
    col_nice_dict = {name: name.replace('qx2_', '') for name in col_name_list}
    col_nice_dict.update({
        'qx2_gt_timedelta': 'GT TimeDelta',
        'qx2_gf_timedelta': 'GF TimeDelta',
        'qx2_gt_rank': 'GT Rank',
    })
    editable_colnames = []
    sortby = 'qaids'
    def get_thumb_size():
        return 128
    col_width_dict = {}
    custom_api = guitool.CustomAPI(
        col_name_list, col_types_dict, col_getter_dict,
        col_bgrole_dict, col_ider_dict, col_setter_dict,
        editable_colnames, sortby, get_thumb_size,
        sort_reverse=True,
        col_width_dict=col_width_dict,
        col_nice_dict=col_nice_dict
    )
    #headers = custom_api.make_headers(tblnice='results')
    #print(ut.dict_str(headers))
    wgt = MetadataViewer()
    wgt.connect_api(custom_api)
    return wgt


def make_test_result_custom_api(ibs, testres):
    import guitool
    guitool.ensure_qapp()
    cfgx = 0
    cfgres_info = testres.cfgx2_cfgresinfo[cfgx]
    qaids = testres.qaids
    gt_aids = cfgres_info['qx2_gt_aid']
    gf_aids = cfgres_info['qx2_gf_aid']
    qx2_gt_timedelta = ibs.get_annot_pair_timdelta(qaids, gt_aids)
    qx2_gf_timedelta = ibs.get_annot_pair_timdelta(qaids, gf_aids)
    col_name_list = [
        'qaids',
        'qx2_gt_aid',
        'qx2_gf_aid',
        'qx2_gt_timedelta',
        'qx2_gf_timedelta',
    ]
    col_types_dict = {}
    col_getter_dict = {}
    col_getter_dict.update(**cfgres_info)
    col_getter_dict['qaids'] = testres.qaids
    col_getter_dict['qx2_gt_timedelta'] = qx2_gt_timedelta
    col_getter_dict['qx2_gf_timedelta'] = qx2_gf_timedelta
    col_bgrole_dict = {}
    col_ider_dict = {}
    col_setter_dict = {}
    editable_colnames = []
    sortby = 'qaids'
    def get_thumb_size():
        return 128
    col_width_dict = {}

    custom_api = guitool.CustomAPI(
        col_name_list, col_types_dict, col_getter_dict,
        col_bgrole_dict, col_ider_dict, col_setter_dict,
        editable_colnames, sortby, get_thumb_size, True, col_width_dict)
    #headers = custom_api.make_headers(tblnice='results')
    #print(ut.dict_str(headers))
    wgt = guitool.APIItemWidget()
    wgt.connect_api(custom_api)
    return wgt
