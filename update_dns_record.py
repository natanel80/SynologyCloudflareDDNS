#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import sys


class APIError(Exception):
    pass


class ZoneNotFoundError(Exception):
    pass


class RecordNotFoundError(Exception):
    pass


class AuthenticationError(Exception):
    pass


def main():
    if len(sys.argv) != 5:
        print('Usage: update_dns_record.py <zone_id> <password> <hostname> <ip>')
        sys.exit(1)

    zone_id = sys.argv[1]
    api_token = sys.argv[2]
    hostname = sys.argv[3]
    ip = sys.argv[4]

    try:
        updater = CloudflareUpdater(api_token, zone_id)
        updater.execute(hostname, ip)
        print('good')
    except ZoneNotFoundError:
        print('nohost')
    except RecordNotFoundError:
        print('nohost')
    except AuthenticationError:
        print('badauth')
    except APIError as e:
        error_message = str(e)
        if 'abuse' in error_message:
            print('abuse')
        elif 'notfqdn' in error_message:
            print('notfqdn')
        elif 'badagent' in error_message:
            print('badagent')
        elif 'badresolv' in error_message:
            print('badresolv')
        elif 'badconn' in error_message:
            print('badconn')
        else:
            print('911')
    except Exception as e:
        print(f'Error: {e}')
        print('911')


class CloudflareUpdater:
    def __init__(self, api_token, zone_id):
        self.api_token = api_token
        self.zone_id = zone_id
        self.base_url = 'https://api.cloudflare.com/client/v4/'

    def execute(self, record_name, ip):
        record_id, current_ip = self._query_record(record_name)
        if current_ip == ip:
            print('nochg')
        else:
            self._update_record(record_id, record_name, ip)

    def _query_record(self, record_name):
        url = f'{self.base_url}zones/{self.zone_id}/dns_records?name={record_name}&type=A'
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }
        response = requests.get(url, headers=headers)
        result = response.json()

        if not result['success']:
            raise APIError(result['errors'])

        if len(result['result']) != 1:
            raise RecordNotFoundError(f'Record not found: {record_name}')

        record = result['result'][0]
        return record['id'], record['content']

    def _update_record(self, record_id, record_name, ip):
        url = f'{self.base_url}zones/{self.zone_id}/dns_records/{record_id}'
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }
        data = {
            'type': 'A',
            'name': record_name,
            'content': ip,
            'ttl': 1,
            'proxied': False
        }
        response = requests.put(url, headers=headers, data=json.dumps(data))
        result = response.json()

        if not result['success']:
            raise APIError(result['errors'])


if __name__ == '__main__':
    main()
