from __future__ import absolute_import, division, print_function
import six
import utool  # NOQA
import utool as ut
from ibeis import constants
from os.path import dirname, join
import ibeis.control.template_definitions as Tdef


STRIP_DOCSTR   = False
USE_SHORTNAMES = True


class SHORTNAMES(object):
    ANNOT      = 'annot'
    CHIP       = 'chip'
    FEAT       = 'feat'
    FEATWEIGHT = 'featweight'
    RVEC       = 'residual'  # 'rvec'
    VOCABTRAIN = 'vocabtrain'
    DETECT     = 'detect'

depends_map = {
    SHORTNAMES.ANNOT: None,
    SHORTNAMES.CHIP: SHORTNAMES.ANNOT,
    SHORTNAMES.FEAT: SHORTNAMES.CHIP,
    SHORTNAMES.FEATWEIGHT: SHORTNAMES.FEAT,
    SHORTNAMES.RVEC:       SHORTNAMES.FEAT,
}

# shortened tablenames
tablename2_tbl = {
    constants.ANNOTATION_TABLE     : SHORTNAMES.ANNOT,
    constants.CHIP_TABLE           : SHORTNAMES.CHIP,
    constants.FEATURE_TABLE        : SHORTNAMES.FEAT,
    constants.FEATURE_WEIGHT_TABLE : SHORTNAMES.FEATWEIGHT,
    constants.RESIDUAL_TABLE       : SHORTNAMES.RVEC,
}

# mapping to variable names in constants
tbl2_tablename = ut.invert_dict(tablename2_tbl)
tbl2_TABLE = {key: ut.get_varname_from_locals(val, constants.__dict__)
              for key, val in six.iteritems(tbl2_tablename)}

# Lets just use strings in autogened files for now: TODO: use constant vars
# later
#tbl2_TABLE = {key: '\'%s\'' % (val,) for key, val in six.iteritems(tbl2_tablename)}
tbl2_TABLE = {key: 'constants.' + ut.get_varname_from_locals(val, constants.__dict__)
                for key, val in six.iteritems(tbl2_tablename)}


variable_aliases = {
    #'chip_rowid_list': 'cid_list',
    #'annot_rowid_list': 'aid_list',
    #'feature_rowid_list': 'fid_list',
    'chip_rowid': 'cid',
    'annot_rowid': 'aid',
    'feat_rowid': 'fid',
    'num_feats': 'nFeats',
    'featweight_forground_weight': 'fgweight',
    'keypoints': 'kpts',
    'vectors': 'vecs',
    'residualvecs': 'rvecs',
}


def format_controller_func(func_code):
    """
    CommandLine:
        python ibeis/control/templates.py
    """
    # BOTH OPTIONS ARE NOT GARUENTEED TO WORK. If there are bugs here may be a
    # good place to look.
    func_code = ut.regex_replace(r'^ *# STARTBLOCK *$\n', '', func_code)
    func_code = ut.regex_replace(r'^ *# ENDBLOCK *$\n?', '', func_code)
    if STRIP_DOCSTR:
        # might not always work. newline hacks away dumb blank line
        func_code = ut.regex_replace('""".*"""\n    ', '', func_code)
    if USE_SHORTNAMES:
        # Execute search and replaces without changing strings
        func_code = ut.replace_nonquoted_text(func_code,
                                              variable_aliases.keys(),
                                              variable_aliases.values())
    # ensure pep8 formating
    #func_code = ut.autofix_codeblock(func_code).strip()
    # add decorators
    func_code = '@register_ibs_method\n' + func_code
    return func_code


def build_dependent_controller_funcs(tablename, tableinfo):

    # -----
    # Setup
    # -----

    (dbself, all_colnames, superkey_colnames, primarykey_colnames, other_colnames) = tableinfo
    #
    nonprimary_child_colnames = ut.setdiff_ordered(all_colnames, primarykey_colnames)
    child_other_propnames = ', '.join(other_colnames)
    child_other_propname_lists = ', '.join([colname + '_list' for colname in other_colnames])
    # for the preproc_tbe.compute... method
    child_props = '_'.join(other_colnames)
    superkey_args = ', '.join([colname + '_list' for colname in superkey_colnames])

    fmtdict = {
    }

    fmtdict['nonprimary_child_colnames'] = nonprimary_child_colnames
    fmtdict['child_other_propnames'] = child_other_propnames
    fmtdict['child_other_propname_lists'] = child_other_propname_lists
    fmtdict['child_props'] = child_props
    fmtdict['superkey_args'] = superkey_args
    fmtdict['self'] = 'ibs'
    fmtdict['dbself'] = dbself

    CONSTANT_COLNAMES = []
    functype2_func_list = ut.ddict(list)
    constant_list = []

    # ----------------------------
    # Format dict helper functions
    # ----------------------------

    def _setupper(fmtdict, key, val):
        fmtdict[key] = val
        fmtdict[key.upper()] = val.upper()

    def set_parent_child(parent, child):
        _setupper(fmtdict, 'parent', parent)
        _setupper(fmtdict, 'child', child)

    def set_root_leaf(root, leaf, leaf_parent):
        _setupper(fmtdict, 'root', root)
        _setupper(fmtdict, 'leaf', leaf)
        _setupper(fmtdict, 'leaf_parent', leaf_parent)
        fmtdict['LEAF_TABLE'] = tbl2_TABLE[leaf]  # tblname1_TABLE[child]

    def set_tbl(tbl):
        _setupper(fmtdict, 'tbl', tbl)
        fmtdict['TABLE'] = tbl2_TABLE[tbl]

    def append_func(func_code_fmtstr, func_type):
        func_code = func_code_fmtstr.format(**fmtdict)
        func_code = format_controller_func(func_code)
        functype2_func_list[func_type].append(func_code)

    def append_constant(varname, valstr):
        const_fmtstr = varname + ' = \'%s\'' % (valstr,)
        constant_list.append(const_fmtstr.format(**fmtdict))

    CONSTANT_COLNAMES.extend(other_colnames)

    # ----------------------------
    # Build dependency path
    # ----------------------------

    child = tablename2_tbl[tablename]
    depends_list = build_depends_path(child)

    set_root_leaf(depends_list[0], depends_list[-1], depends_list[-2])

    # ----------------------------
    # Parent-Child dependant rowid lines
    # ----------------------------

    pc_dependant_rowid_lines = []
    for parent, child in ut.itertwo(depends_list):
        set_parent_child(parent, child)
        # rowid constants
        append_constant('{CHILD}_ROWID', '{child}_rowid')
        append_constant('{PARENT}_ROWID', '{parent}_rowid')
        # depenant rowid lines
        pc_dependant_rowid_lines.append(Tdef.Tline_pc_dependant_rowid.format(**fmtdict))
    fmtdict['pc_dependant_rowid_lines'] = ut.indent(ut.indentjoin(pc_dependant_rowid_lines))

    # Getter template: config_rowid
    append_func(Tdef.Tgetter_rl_dependant_all_rowids, 'getter_rl_dependant')
    append_func(Tdef.Tgetter_rl_dependant_rowids, 'getter_rl_dependant')

    other_cols = list(map(lambda colname: colname2_col(colname, tablename), other_colnames))
    other_COLNAMES = list(map(lambda colname: colname.upper(), other_colnames))

    for colname, col, COLNAME in zip(other_colnames, other_cols, other_COLNAMES):
        fmtdict['COLNAME'] = COLNAME
        fmtdict['col'] = col
        # Getter template: dependant columns
        for parent, child in ut.itertwo(depends_list):
            set_parent_child(parent, child)
            fmtdict['TABLE'] = tbl2_TABLE[child]  # tblname1_TABLE[child]
            #append_func(Tdef.Tgetter_pc_dependant_column, 'dependant_property')
        # Getter template: native (Level 0) columns
        set_tbl(child)
        append_func(Tdef.Tgetter_table_column, 'table_column')
        append_func(Tdef.Tgetter_rl_pclines_dependant_column, 'rl_table_column')
        constant_list.append(COLNAME + ' = \'%s\'' % (colname,))
        append_constant(COLNAME, colname)

    append_func(Tdef.Tgetter_native_rowid_from_superkey, 'ider')
    append_func(Tdef.Tcfg_config_rowid_getter, 'config_rowid')
    append_func(Tdef.Tgetter_native_rowid_from_superkey, 'getter_superkey')
    append_func(Tdef.Tadder_dependant_child, 'adder_dependant')

    return functype2_func_list, constant_list


#def test():
#    from ibeis.control.templates import *  # NOQA

def build_depends_path(child):
    parent = depends_map[child]
    if parent is not None:
        return build_depends_path(parent) + [child]
    else:
        return [child]
    #depends_list = ['annot', 'chip', 'feat', 'featweight']


def colname2_col(colname, tablename):
    # col is a short alias for colname
    col = colname.replace(ut.singular_string(tablename) + '_', '')
    return col


def get_tableinfo(tablename, ibs=None):
    dbself = None
    tableinfo = None
    if ibs is not None:
        valid_db_tablenames = ibs.db.get_table_names()
        valid_dbcache_tablenames = ibs.dbcache.get_table_names()

        sqldb = None
        if tablename in valid_db_tablenames:
            sqldb = ibs.db
            dbself = 'db'
        elif tablename in valid_dbcache_tablenames:
            if sqldb is not None:
                raise AssertionError('Tablename=%r is specified in both schemas' % tablename)
            sqldb = ibs.dbcache
            dbself = 'dbcache'
        else:
            print('WARNING unknown tablename=%r' % tablename)

        if sqldb is not None:
            all_colnames = sqldb.get_column_names(tablename)
            superkey_colnames = sqldb.get_table_superkey_colnames(tablename)
            primarykey_colnames = sqldb.get_table_primarykey_colnames(tablename)
            other_colnames = sqldb.get_table_otherkey_colnames(tablename)
    if dbself is None:
        dbself = 'dbunknown'
        all_colnames        = []
        superkey_colnames   = []
        primarykey_colnames = []
        other_colnames      = []
        if tablename == constants.FEATURE_WEIGHT_TABLE:
            dbself = 'dbcache'
            all_colnames = ['feature_weight_fg']
    if tablename == constants.RESIDUAL_TABLE:
        other_colnames.append('rvecs')
    tableinfo = (dbself, all_colnames, superkey_colnames, primarykey_colnames, other_colnames)
    return tableinfo


def main(ibs):
    """
    CommandLine:
        python dev.py --db testdb1 --cmd
        %run dev.py --db testdb1 --cmd
    """
    tblname_list = [
        #constants.CHIP_TABLE,
        #constants.FEATURE_TABLE,
        constants.FEATURE_WEIGHT_TABLE,
        #constants.RESIDUAL_TABLE
    ]
    #child = 'featweight'
    tblname2_functype2_func_list = ut.ddict(lambda: ut.ddict(list))
    constant_list_ = [
        'CONFIG_ROWID = \'config_rowid\'',
        'FEATWEIGHT_ROWID = \'featweight_rowid\'',
    ]
    for tablename in tblname_list:
        tableinfo = get_tableinfo(tablename, ibs)

        functype2_func_list, constant_list = build_dependent_controller_funcs(tablename, tableinfo)
        constant_list_.extend(constant_list)
        tblname2_functype2_func_list[tablename] = functype2_func_list

    functype_set = set([])
    for tblname, val in six.iteritems(tblname2_functype2_func_list):
        for functype in six.iterkeys(val):
            functype_set.add(functype)
    functype_list = list(functype_set)

    body_codeblocks = []

    # Append constants to body
    aligned_constants = '\n'.join(ut.align_lines(sorted(list(set(constant_list_)))))
    body_codeblocks.append('# AUTOGENED CONSTANTS:\n' + aligned_constants)

    # Append functions to body
    seen = set([])
    for count1, functype in enumerate(functype_list):
        functype_codeblocks = []
        functype_section_header = ut.codeblock(
            '''
            # =========================
            # {FUNCTYPE} METHODS
            # =========================
            '''
        ).format(FUNCTYPE=functype.upper())
        functype_codeblocks.append(functype_section_header)
        for count, item in enumerate(six.iteritems(tblname2_functype2_func_list)):
            tblname, val = item
            functype_table_section_header = ut.codeblock(
                '''
                #
                # {functype} tablename='{tblname}'
                '''
            ).format(functype=functype, tblname=tblname)
            functype_codeblocks.append(functype_table_section_header)
            for func_codeblock in val[functype]:
                if func_codeblock in seen:
                    continue
                seen.add(func_codeblock)
                functype_codeblocks.append(func_codeblock)
        body_codeblocks.extend(functype_codeblocks)

    autogen_fpath = join(ut.truepath(dirname(ibeis.control.__file__)), '_autogen_ibeiscontrol_funcs.py')

    autogen_header = Tdef.Theader_ibeiscontrol.format(timestamp=ut.get_timestamp('printable'))
    #from ibeis.constants import (IMAGE_TABLE, ANNOTATION_TABLE, LBLANNOT_TABLE,
    #                             ENCOUNTER_TABLE, EG_RELATION_TABLE,
    #                             AL_RELATION_TABLE, GL_RELATION_TABLE,
    #                             CHIP_TABLE, FEATURE_TABLE, LBLIMAGE_TABLE,
    #                             CONFIG_TABLE, CONTRIBUTOR_TABLE, LBLTYPE_TABLE,
    #                             METADATA_TABLE, VERSIONS_TABLE, __STR__)

    autogen_body = '\n\n'
    autogen_body += ('\n\n\n'.join(body_codeblocks))

    autogen_text = '\n'.join([autogen_header, autogen_body, ''])

    if ut.get_flag('--dump-autogen-controller'):
        ut.write_to(autogen_fpath, autogen_text)
    else:
        print(autogen_text)

    return locals()


if __name__ == '__main__':
    """
    CommandLine:
        python ibeis/control/templates.py
        python ibeis/control/templates.py --dump-autogen-controller
    """
    if 'ibs' not in vars():
        import ibeis
        ibs = ibeis.opendb('testdb1')
    locals_ = main(ibs)
    exec(ut.execstr_dict(locals_))
