#!/usr/bin/python

import logging
import base64
import urllib2
import json
import requests
import argparse

"""
add the SCC fully qualified hostname and access_code below
save the script as mvApp.py
run the script "mvApp.py <from_group_id> <to_group_id>"
"""

# Fully qualified hostname as string in single quotes
HOSTNAME = 'riverbedscc.lagermann.com'

# Access code generated from the appliance in single quotes
ACCESS_CODE = 'eyJhdWQiOiAiaHR0cHM6Ly9SaXZlcmJlZENNQy5sYWdlcm1hbm4uY29tL2FwaS9jb21tb24vMS4wL3Rva2VuIiwgImlzcyI6ICJo' \
              'dHRwczovL1JpdmVyYmVkQ01DLmxhZ2VybWFubi5jb20iLCAicHJuIjogImFkbWluIiwgImp0aSI6ICI1NmVjNmQyMy0zYjQxLTRk' \
              'MDctYjY3Zi1lZmE4ODJhODQ1MjciLCAiZXhwIjogIjAiLCAiaWF0IjogIjEzODQyNjcwNTQifQ=='

# Do not modify below this comment!  Do not modify below this comment!  Do not modify below this comment!
# ------------------------------------------------------------------------------------------------------------------
#
# Application group_id's
application_group_id = {
    '1': 'Business Bulk',
    '2': 'Business Critical',
    '3': 'Business Productivity',
    '4': 'Business Standard',
    '5': 'Business VDI',
    '6': 'Business Video',
    '7': 'Business Voice',
    '8': 'Recreational',
    '9': 'Standard Bulk',
    '10': 'Custom Applications'
}


PROTOCOL = "https"
# API URI template
API_URL = PROTOCOL + "://" + HOSTNAME + "/api/cmc.applications/2.0/{0}"

# API resource to execute
RESOURCE = "applications"

GROUP_RESOURCE = "groups"


def validate_args():
    if args.from_group and not args.to_group:
        print('Cannot specify a from_group without a to_group')
        exit(1)

    if args.to_group and not args.from_group:
        print('Cannot specify a to_group without a from_group')
        exit(1)

    if args.built_in_only and not (args.to_group and args.from_group):
        print ('Cannot specify built_in_only without a to_group and a from_group')
        exit(1)

    if args.restore and (args.collect or args.from_group or args.to_group or args.group_restore or args.built_in_only):
        print('Cannot specify restore with any other option.')
        exit(1)

    if args.collect and (args.restore or args.from_group or args.to_group or args.group_restore or args.built_in_only):
        print('Cannot specify collect with any other option.')
        exit(1)

    if args.group_restore and (args.restore or args.from_group or args.to_group or args.collect or args.built_in_only):
        print('Cannot specify group_restore with any other option.')
        exit(1)


def encode(s):
    return base64.urlsafe_b64encode(s)


def init_mp_logger(logger_filename, name=None):

    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    fh = logging.FileHandler(logger_filename)
    fh.setLevel(logging.WARNING)

    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def request_body(access_code):
    """
    This method prepares the request to be
    sent to the oauth REST API

    @param access_code: Access code from appliance
    """

    header_encoded = encode("{\"alg\":\"none\"}\n")

    payload = access_code
    payload_str = ''.join(payload)

    signature_encoded = ''

    assertion = '.'.join([header_encoded, payload_str])
    assert_str = assertion.rstrip()

    assert_str2 = '.'.join([assert_str, signature_encoded])

    grant_type = 'access_code'
    state = 'a34rfFas'

    data = 'grant_type=%s&assertion=%s&state=%s' % (
        grant_type, assert_str2, state)

    return data


def get_access_token(hostname, request_body):
    """
    This method makes an oauth REST API call and gets the access token
    from appliance/resource owner

    @param hostname: Appliance name
    @param request_body: Request for making REST call
    """

    api_url = "https://{0}/api/common/1.0/oauth/token"
    req = urllib2.Request(url=api_url.format(hostname),
                          data=request_body)
    f = urllib2.urlopen(req)
    data = f.read()
    decoded_data = json.loads(data)
    """
    resp = requests.post(url, data=json.dumps(input_data), headers=headers, verify=False)
    """

    payload = decoded_data['access_token'].strip()
    payload_str = ''.join(payload)

    return "Authorization: Bearer %s" % payload_str


def do_put_data(data, headers, to_group_id):
    # build the URL to request all the data for the application to be moved
    url = API_URL.format(RESOURCE) + "/items/" + str(data['id'])
    # get request to the SCC to collect all the data for the application to be moved
    resp = requests.get(url, headers=headers, verify=False)
    # store the data collected
    new_data = resp.json()
    # collect the name of the application for logging
    app = new_data['name']
    # collect the old group_id for logging
    from_group_id = new_data['group_id']
    # replace the old group_id in new_data with the new group_id
    new_data['group_id'] = int(to_group_id)
    # put request to push all the old data with the new group_id back to the SCC
    requests.put(url, data=json.dumps(new_data), verify=False, headers=headers)
    # log the application that was moved to include the to and from group names and ID's
    logger.warning('Moved application ID:' +
                   str(data['id']) + ' (' + str(app) + ') from group ID:' +
                   str(from_group_id) + ' (' + application_group_id[str(from_group_id)] + ') to group ID:' +
                   str(to_group_id) + ' (' + application_group_id[str(to_group_id)] + ')')


def collect_rest_api(access_token):

    try:
        auth = access_token.split(":")
        headers = {'Content-Type': 'application/json',
                   auth[0]: auth[1]
                   }
        url = API_URL.format(RESOURCE)
        resp = requests.get(url, headers=headers, verify=False)

        data = resp.json()

        appList = []

        for app in data:
            app_obj = {}
            app_obj['app_id'] = app['id']
            app_obj['app_name'] = app['name']
            app_obj['group_name'] = app['group_name']
            for tag in app['tags']:
                if app['group_name'] == tag['name']:
                    app_obj['group_id'] = tag['id']

            appList.append(app_obj)

        fh = open('defaultGroups.txt', 'w')
        json.dump(appList, fh)
        fh.close()
        logger.warning('The file defaultGroups.txt has been created, store it in a safe place!')

    except Exception, e:
        print e.message


def group_rest_api(access_token):

    try:
        auth = access_token.split(":")
        headers = {'Content-Type': 'application/json',
                   auth[0]: auth[1]
                   }
        url = API_URL.format(RESOURCE)
        resp = requests.get(url, headers=headers, verify=False)
        data = resp.json()
        with open('defaultGroups.txt') as default_groups:
            default_data = json.load(default_groups)

        if to_group_id == 10:
            for id in data:
                if not id['is_built_in']:
                    do_put_data(id, headers, to_group_id)
        else:
            for id in data:
                if id['is_built_in']:
                    default_gen = (item for item in default_data if item['app_id'] == id['id'])
                    for item in default_gen:
                        if item['group_id'] == to_group_id:
                            do_put_data(id, headers, to_group_id)
                        break

    except Exception, e:
        print e.message


def restore_rest_api(access_token):

    try:
        auth = access_token.split(":")
        headers = {'Content-Type': 'application/json',
                   auth[0]: auth[1]
                   }
        url = API_URL.format(RESOURCE)
        resp = requests.get(url, headers=headers, verify=False)
        data = resp.json()
        with open('defaultGroups.txt') as default_groups:
            default_data = json.load(default_groups)

        for id in data:
            if id['is_built_in']:
                default_gen = (item for item in default_data if item['app_id'] == id['id'])
                for item in default_gen:
                    to_group_id = item['group_id']
                    do_put_data(id, headers, to_group_id)
                    break
            else:
                to_group_id = 10
                do_put_data(id, headers, to_group_id)

    except Exception, e:
        print e.message


def execute_rest_api(access_token):

    try:
        auth = access_token.split(":")
        headers = {'Content-Type': 'application/json',
                   auth[0]: auth[1]
                   }
        url = API_URL.format(GROUP_RESOURCE) + "/items/" + str(from_group_id)
        resp = requests.get(url, headers=headers, verify=False)

        data = resp.json()
        for d in data['applications']:
            if args.built_in_only:
                if d['is_built_in']:
                    do_put_data(d, headers, to_group_id)
                else:
                    continue
            else:
                do_put_data(d, headers, to_group_id)

    except Exception, e:
        print e.message


if __name__ == '__main__':
    """
    This is the main method
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--from_group', help="The group_id to remove applications from", type=int)
    parser.add_argument('-t', '--to_group', help="The group_id to move applications to", type=int)
    parser.add_argument('-b', '--built_in_only', action="store_true", dest="built_in_only", default=False,
                        help="Move only default applications, do not move custom apps")
    parser.add_argument('-g', '--group_restore', help="Move a select group of applications to the default group",
                        type=int)
    parser.add_argument('-r', '--restore', action="store_true", dest="restore", default=False,
                        help="Move all applications to their default groups")
    parser.add_argument('-c', '--collect', action="store_true", dest="collect", default=False,
                        help="Create a defaultGroups.txt file from a SCC")
    args = parser.parse_args()
    validate_args()
    from_group_id = args.from_group
    if args.to_group is None:
        to_group_id = args.group_restore
    else:
        to_group_id = args.to_group

    if from_group_id not in range(1, 11) and from_group_id is not None:
        print("group_id's must be between 1 and 10")
        exit(1)

    if to_group_id not in range(1, 11) and from_group_id is not None:
        print("group_id's must be between 1 and 10")
        exit(1)

    hostname = HOSTNAME
    access_code = ACCESS_CODE
    logger_filename = './mvApp.log'
    logger = init_mp_logger(logger_filename)
    request_body = request_body(access_code)
    access_token = get_access_token(hostname, request_body)
    if args.restore:
        api_result = restore_rest_api(access_token)
        print api_result
        print "All applications have been restored to their default groups!"
        exit(0)
    elif args.collect:
        api_result = collect_rest_api(access_token)
        print "The file defaultGroups.txt has been created"
        print "Store it in a safe place!"
        exit(0)
    elif args.group_restore:
        api_result = group_rest_api(access_token)
        print ('All applications from group ID:' + str(to_group_id) + ' (' + application_group_id[str(to_group_id)] + ') have been moved back to group ID:' + str(to_group_id) + ' (' + application_group_id[str(to_group_id)] + ')')
        exit(0)
    else:
        api_result = execute_rest_api(access_token)
        print api_result
        print ('All applications from group ID:' + str(from_group_id) + ' (' + application_group_id[str(from_group_id)] + ') have been moved to group ID:' + str(to_group_id) + ' (' + application_group_id[str(to_group_id)] + ')')

        exit(0)


