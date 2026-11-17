import datetime as dt
import io
import urllib.error
import unittest
from unittest.mock import patch
from bridge_pipeline.core import _google_news_request_root
from bridge_pipeline.run import healthcheck

class RateLimitedSourceTests(unittest.TestCase):
    def test_429_retries_then_real_rss_success(self):
        err=urllib.error.HTTPError('https://news.google.com/rss',429,'Too Many Requests',{'Retry-After':'2'},None)
        response=io.BytesIO(b'<rss><channel></channel></rss>')
        with patch('bridge_pipeline.core.urllib.request.urlopen',side_effect=[err,response]) as get, patch('bridge_pipeline.core.time.sleep') as sleep, patch('bridge_pipeline.core._GOOGLE_NEWS_LAST_REQUEST',0.0):
            root=_google_news_request_root(object())
        self.assertEqual(root.tag,'rss')
        self.assertEqual(get.call_count,2)
        self.assertTrue(any(call.args[0]>=2 for call in sleep.call_args_list))

    def test_persistent_429_is_failure_never_empty_observation(self):
        def limited(*args,**kwargs):
            raise urllib.error.HTTPError('https://news.google.com/rss',429,'Too Many Requests',{},None)
        with patch('bridge_pipeline.core.urllib.request.urlopen',side_effect=limited) as get, patch('bridge_pipeline.core.time.sleep'), patch('bridge_pipeline.core._GOOGLE_NEWS_LAST_REQUEST',0.0):
            with self.assertRaises(urllib.error.HTTPError):
                _google_news_request_root(object())
        self.assertEqual(get.call_count,4)

    def test_discovery_failure_does_not_mask_required_success(self):
        class FakeDB:
            def select(self,*args,**kwargs):
                return [dict(source_id='google_news_discovery',status='failed'),dict(source_id='google_news_rss',status='success'),dict(source_id='opendart',status='success')]
        healthcheck(FakeDB())

    def test_required_news_failure_still_blocks_publication(self):
        class FakeDB:
            def select(self,*args,**kwargs):
                return [dict(source_id='google_news_discovery',status='success'),dict(source_id='google_news_rss',status='failed'),dict(source_id='opendart',status='success')]
        with self.assertRaises(SystemExit):
            healthcheck(FakeDB())

if __name__=='__main__':unittest.main()
