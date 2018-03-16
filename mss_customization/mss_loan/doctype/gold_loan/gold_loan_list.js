frappe.listview_settings['Gold Loan'] = {
  add_fields: ['status', 'foreclosure_date'],
  get_indicator: function({ status, foreclosure_date }) {
    if (status === 'Open') {
      if (moment().isAfter(foreclosure_date)) {
        return [
          __('Lapsed'),
          'orange',
          `status,=,Open|foreclosure_date,<,${frappe.datetime.nowdate()}`,
        ];
      }
      return [__('Open'), 'green', 'status,=,Open'];
    }
    if (status === 'Repaid') {
      return [__('Repaid'), 'lightblue', 'status,=,Repaid'];
    }
    if (status === 'Foreclosed') {
      return [__('Foreclosed'), 'purple', 'status,=,Foreclosed'];
    }
  },
};
