#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
Converts an IBEIS database to a wildbook db
"""
# TODO: ADD COPYRIGHT TAG
from __future__ import absolute_import, division, print_function
#import ibeis
import utool
import json
import requests
from six.moves import zip, map
print, print_, printDBG, rrr, profile = utool.inject(__name__, '[export_wb]')


def export_ibeis_to_wildbook(ibs, imgsetid_list):
    target_url_occurrence = ibs.wbaddr + '/rest/org.ecocean.Occurrence'
    target_url_imageset = ibs.wbaddr + '/rest/org.ecocean.ImageSet'
    target_url_imageset_add_image = ibs.wbaddr + '/ImageSetAddImage'
    target_url_occurrence_add_imageset = ibs.wbaddr + '/OccurrenceAddImageSet'

    # list of tuples, each has the names associated with the imageset
    nids_list = ibs.get_imageset_nids(imgsetid_list)

    assert len(nids_list) == len(imgsetid_list)
    for imgsetid, nids in zip(imgsetid_list, nids_list):
        # the actual names corresponding to the name ids
        names_text = ibs.get_name_texts(nids)
        # list of list of images that correspond to each name id
        gids_lists = ibs.get_name_gids(nids)

        # each name id must have exactly one text name associated with it, as well as one list of image ids
        assert len(nids) == len(names_text) == len(gids_lists)

        # the actual text imageset name corresponding to the imageset id
        imagesettext = ibs.get_imageset_text(imgsetid)

        # ibeis imageset is wildbook occurrence!
        occurrence_id = str(imagesettext)
        payload_create_occurrence = {'groupBehavior': '',
                                     'class': 'org.ecocean.Occurrence',
                                     'occurrenceID': occurrence_id}

        # create a Wildbook Occurrence to represent this IBEIS ImageSet
        response = requests.post(target_url_occurrence, data=json.dumps(payload_create_occurrence))
        print ('POSTed IBEIS ImageSet / Wildbook Occurrence %s to %s with status %d' % (imagesettext, target_url_occurrence, response.status_code))

        # creates wildbook imagesets for each name in an ibeis imageset
        for nid, name_text, gids in zip(nids, names_text, gids_lists):
            # create a unique name for this inidividual by concatenating the imageset and name
            wbenc_name = imagesettext + '_' + str(nid)
            payload_create_imageset = {'dwcImageURL': ibs.wbaddr + '/imagesets/imageset.jsp?number=' + wbenc_name,
                                        'occurrenceID': occurrence_id,
                                        'state': 'unapproved',
                                        'dateInMilliseconds': 100,
                                        'approved': True,
                                        'catalogNumber': wbenc_name,
                                        'recordedBy': 'hotspotter',
                                        'individualID': 'Unassigned',
                                        'class': 'org.ecocean.ImageSet',
                                        'guid': 'MY_CATALOG:MY_SPECIES:' + wbenc_name,
                                        'decimalLatitude': '-1.0',
                                        'decimalLongitude': '-1.0'}

            # create this wildbook imageset
            response = requests.post(target_url_imageset, data=json.dumps(payload_create_imageset))
            print ('POSTed Wildbook ImageSet %s to %s with status %d' % (wbenc_name, target_url_imageset, response.status_code))

            payload_occurrence_add_imageset = {'number': wbenc_name,
                                                'occurrence': occurrence_id}

            # link the wildbook imageset to the wildbook occurrence / ibeis imageset
            response = requests.post(target_url_occurrence_add_imageset, data=json.dumps(payload_occurrence_add_imageset))
            print ('Linked Wildbook ImageSet %s to Wildbook Occurrence %s with status %s' % (wbenc_name, occurrence_id, response.status_code))
            print (response.url)
            # get the paths to all the images in which this name id appears
            paths = ibs.get_image_paths(gids)
            payload_imageset_add_image = {'number': wbenc_name}

            # upload the images one by one
            for path in paths:
                try:
                    with open(path, 'rb') as img_file:
                        response = requests.post(target_url_imageset_add_image, data=payload_imageset_add_image, files={'file': img_file})
                        print ('POSTed %s to %s with status %d' % (path, target_url_imageset_add_image, response.status_code))
                except IOError:
                    print('Could not open file at %s' % (path))
                    continue

            # update the wildbook imageset thumbnail image
            response = requests.post(ibs.wbaddr + '/resetThumbnail.jsp?number=' + wbenc_name + '&imageNum=1')


def export_ibeis_to_wildbook2(ibs, imgsetid_list):
    """ LECACY CODE. DEPRICATE? """
    wbaddr = ibs.wbaddr
    wb_imagesets = {}

    for imageset_id in imgsetid_list:
        imageset = ibs.get_imageset_text(imageset_id)
        # make occurrence id from imagesettext
        name_annotation_mapping = {}
        image_annotation_mapping = {}
        names = ibs.get_imageset_nids(imageset_id)
        annotations = ibs.get_imageset_aids(imageset_id)
        images = ibs.get_imageset_gids(imageset_id)

        for name_id in names:
            wbenc_name = imageset + str(name_id)
            wb_imagesets[name_id] = wbenc_name
            name_annotation_mapping[name_id] = []
            image_annotation_mapping[name_id] = []

        for annotation_id in annotations:
            assoc_name_id = ibs.get_annot_name_rowids([annotation_id])[0]
            name_annotation_mapping[assoc_name_id].append(annotation_id)

        print (ibs.get_image_nids(images))
        #for img_id in images:
        #    print (ibs.get_image_nids([img_id]))
        #    assoc_name_id = ibs.get_image_nids([img_id])[0]
        #    image_annotation_mapping[assoc_name_id].append(img_id)

        #print (names)
        for name_id in names:
            wbenc_name = wb_imagesets[name_id]
            annotation_id_list = name_annotation_mapping[name_id]
            image_id_list = image_annotation_mapping[name_id]
            print (image_id_list)
            wbenc_time_avg = int(sum(ibs.get_image_unixtime(ibs.get_annot_gids(annotation_id_list))) / len(annotation_id_list))

            lat, lng = list(map(lambda x: sum(x) / len(x), zip(*ibs.get_image_gps(ibs.get_annot_gids(annotation_id_list)))))
            print (lat)
            print (lng)
            print (wbenc_time_avg)
            # TODO: Pass the verts, theta, and name_uuid
            payload_imageset = {'dwcImageURL': wbaddr + '/imagesets/imageset.jsp?number=' + wbenc_name,  # NOQA
                                 'state': 'unapproved',
                                 'dateInMilliseconds': wbenc_time_avg,
                                 'approved': True,
                                 'catalogNumber': wbenc_name,
                                 'recordedBy': 'hotspotter',
                                 'individualID': 'Unassigned',
                                 'class': 'org.ecocean.ImageSet',
                                 'guid': 'MY_CATALOG:MY_SPECIES:' + wbenc_name,
                                 'decimalLatitude': str(lat),
                                 'decimalLongitude': str(lng)}

            # make occurrence ID part of the request

            #response = requests.post(wbaddr + '/rest/org.ecocean.ImageSet', data=json.dumps(payload_imageset))
            #print (response.status_code)
