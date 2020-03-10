import { Ng2AutoCompleteKerasPage } from './app.po';

describe('NTU Auto-complete App', function() {
  let page: Ng2AutoCompleteKerasPage;

  beforeEach(() => {
    page = new Ng2AutoCompleteKerasPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
